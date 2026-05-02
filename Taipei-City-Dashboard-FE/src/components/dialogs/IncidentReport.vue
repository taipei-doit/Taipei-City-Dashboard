<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, onMounted, watch } from "vue";
import mapboxGl from "mapbox-gl";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";
import { useAuthStore } from "../../store/authStore";
import http from "../../router/axios";

import DialogContainer from "./DialogContainer.vue";

const dialogStore = useDialogStore();
const mapStore = useMapStore();
const authStore = useAuthStore();

const incidentType = ref("suspected-food-poisoning");
const incidentDesc = ref("");
const incidentDis = ref(0.5);

const typeOptions = [
  { label: "疑似食物中毒", value: "suspected-food-poisoning" },
  { label: "食材/餐點異味", value: "spoiled-food" },
  { label: "環境衛生異常", value: "hygiene-issue" },
  { label: "標示或保存不實", value: "mislabeling" },
  { label: "其他", value: "other" },
];

const disOptions = [
  { label: "500公尺內", value: 0.5 },
  { label: "500公尺~2公里", value: 2 },
  { label: "2公里~5公里", value: 5 },
  { label: "大於5公里", value: 10 },
];

// New: use business name search instead of distance selection
const businessName = ref("");
const searchResults = ref([]); // local restaurant data
const foundLocation = ref(null); // selected feature
let restaurantData = [];

// Load restaurant data on mount
async function loadRestaurantData() {
  try {
    const res = await fetch("/mapData/restaurants.json");
    restaurantData = await res.json();
  } catch (e) {
    console.error("Failed to load restaurant data:", e);
  }
}

// Real-time search as user types
async function performSearch(query) {
  if (!authStore.token) {
    searchResults.value = [];
    return;
  }
  if (!query || query.trim().length === 0) {
    searchResults.value = [];
    return;
  }
  try {
    // Load data if not yet loaded
    if (restaurantData.length === 0) {
      await loadRestaurantData();
    }

    // Search restaurants by name (fuzzy/partial match)
    const queryLower = query.toLowerCase();
    const matches = restaurantData.filter((r) =>
      r.name.toLowerCase().includes(queryLower)
    );

    if (matches && matches.length > 0) {
      // Convert to feature format and add distance
      const features = matches
        .slice(0, 15) // limit to top 15 results
        .map((r) => ({
          center: [r.longitude, r.latitude],
          place_name: r.name,
          address: r.address,
        }));

      const userLat = mapStore.userLocation.latitude;
      const userLng = mapStore.userLocation.longitude;
      if (userLat && userLng) {
        features.forEach((f) => {
          const [lng, lat] = f.center;
          f.distance = distanceKm(userLat, userLng, lat, lng);
        });
        features.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      }
      searchResults.value = features;
    } else {
      searchResults.value = [];
    }
  } catch (e) {
    searchResults.value = [];
  }
}

// Watch businessName input for real-time search
watch(businessName, (newVal) => {
  performSearch(newVal);
});

function distanceKm(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function formatDistanceKm(km) {
  if (km == null) return "";
  if (km < 1) return Math.round(km * 1000) + " m";
  return km.toFixed(2) + " km";
}

function selectResult(feature) {
  if (!feature || !feature.center) return;
  foundLocation.value = feature;
  const [lng, lat] = feature.center;
  mapStore.tempMarkerCoordinates = { lng, lat };
  if (mapStore.popup) {
    mapStore.popup.remove();
    mapStore.popup = null;
  }
  if (mapStore.marker && mapStore.map) {
    mapStore.marker.setLngLat({ lng, lat }).addTo(mapStore.map);
    const popupTitle = feature.place_name || "";
    const popupAddress = feature.address || "";
    const popupHtml = popupAddress
      ? `<div style="font-weight:600; font-size:14px; margin-bottom:2px;">${popupTitle}</div><div style="font-size:12px; color:#666; line-height:1.4;">${popupAddress}</div>`
      : `<div style="font-weight:600; font-size:14px;">${popupTitle}</div>`;
    mapStore.popup = new mapboxGl.Popup({ closeOnClick: false, closeButton: true })
      .setLngLat({ lng, lat })
      .setHTML(popupHtml)
      .addTo(mapStore.map);
    mapStore.map.easeTo({ center: [lng, lat], zoom: 16 });
  }
  // clear results list after selection
  searchResults.value = [];
}

function handleClose() {
	dialogStore.hideAllDialogs();
}

function handleLogin() {
  dialogStore.hideAllDialogs();
  dialogStore.showDialog("login");
}

async function handleSubmit() {
  if (!authStore.token) {
    dialogStore.showDialog("login");
    return;
  }
  if (!mapStore.tempMarkerCoordinates) {
    dialogStore.showNotification("error", "請先搜尋並選擇通報位置");
    return;
  }
  if (mapStore.popup) {
    mapStore.popup.remove();
    mapStore.popup = null;
  }
  const { lng, lat } = mapStore.tempMarkerCoordinates;
  let payload = {
    inctype: incidentType.value,
    description: incidentDesc.value,
    latitude: lat,
    longitude: lng,
    place: foundLocation.value
      ? `${foundLocation.value.place_name}${foundLocation.value.address ? `\n${foundLocation.value.address}` : ""}`
      : "",
    distance: foundLocation.value?.distance || 0.5,
    status: "pending",
  };
  const response = await http.post("/incident/public/", payload);
  incidentType.value = "suspected-food-poisoning";
	incidentDesc.value = "";
  incidentDis.value = 0.5;
  dialogStore.showNotification("success", "食安通報已送出");
	dialogStore.hideAllDialogs();
  mapStore.tempMarkerCoordinates = null;
  foundLocation.value = null;

  try {
    await mapStore.fetchIncidents();
  } catch (error) {
    console.error("Failed to refresh incident markers:", error);
    const incident = response.data?.data;
    if (incident && mapStore.map) {
      mapStore.incidents = [incident, ...mapStore.incidents];
      mapStore.renderIncidents();
    }
  }
}

onMounted(() => {
	mapStore.setCurrentLocation();
	loadRestaurantData();
});
</script>

<template>
  <DialogContainer
    :dialog="`incidentReport`"
    @on-close="handleClose"
  >
    <div v-if="authStore.token" class="incidentreport">
      <h2>食安事件通報</h2>
      <p class="incidentreport-note">通報後會立即出現在地圖上，供管理人員追蹤處理。</p>
      <label> 事件類型 </label>
      <select v-model="incidentType">
        <option
          v-for="(option, index) in typeOptions"
          :key="index"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>

      <label> 事件描述 ({{ incidentDesc.length }}/30) </label>
      <input
        v-model="incidentDesc"
        type="text"
        placeholder="(請概述食安異常情況)"
        required
        :maxlength="30"
      >
      <!-- removed impact range select; use business name search instead -->
      <label> 店家名稱搜尋 </label>
      <input v-model="businessName" type="text" placeholder="輸入店家名稱（即時搜尋）" />
      <div v-if="searchResults.length > 0" class="incidentreport-search-results">
        <p style="margin:6px 0 4px; font-size:var(--font-s); color:var(--color-complement-text)">請選擇分店：</p>
        <ul style="max-height:140px; overflow:auto; padding-left:12px; margin:0">
          <li v-for="(r, i) in searchResults" :key="i" style="margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; gap:8px;">
            <div style="flex:1">
              <div>{{ r.place_name }}</div>
              <div style="font-size:var(--font-s); color:var(--color-complement-text)">{{ r.distance ? formatDistanceKm(r.distance) : '' }}</div>
            </div>
            <button @click="selectResult(r)">選擇</button>
          </li>
        </ul>
      </div>
      <label> 通報位置 (搜尋結果) </label>
      <input
        :value="foundLocation ? (foundLocation.place_name || (foundLocation.center[1] + ', ' + foundLocation.center[0])) : ''"
        disabled
      />
      <label> 通報時間 </label>
      <input
        :value="new Date().toLocaleString()"
        disabled
      >
      <div class="incidentreport-control">
        <button
          v-if="mapStore.tempMarkerCoordinates && incidentDesc"
          class="incidentreport-control-confirm"
          @click="handleSubmit"
        >
          提交
        </button>
      </div>
    </div>
    <div v-else class="incidentreport">
      <h2>需先登入</h2>
      <p class="incidentreport-note">請先登入才能使用食安事件通報功能。</p>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button @click="handleLogin">登入</button>
        <button @click="handleClose">關閉</button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.incidentreport {
	width: 300px;
	display: flex;
	flex-direction: column;

  &-note {
    margin: 0 0 8px;
    font-size: var(--font-s);
    color: var(--color-complement-text);
  }

	label {
		margin: 8px 0 4px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
	}

	&-control {
		height: 27px;
		display: flex;
		justify-content: flex-end;
		margin-top: var(--font-ms);

		&-confirm {
			margin: 0 2px;
			padding: 4px 10px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}
}
</style>
