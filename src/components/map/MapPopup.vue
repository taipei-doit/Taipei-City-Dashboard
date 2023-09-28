<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component is mounted programmically by the mapstore. "mapConfig" and "popupContent" are passed in in the mapStore -->
<script setup>
</script>

<template>
	<!-- <div class="mappopup">
        <button>{{ mapConfig.title }}</button>
        <div>
            <div class="mappopup-content" v-for="item in mapConfig.property" :key="item.key">
                <h3>{{ item.name }}</h3>
                <p>{{ popupContent.properties[item.key] }}</p>
            </div>
        </div>
    </div> -->
	<div class="mappopup">
		<div class="mappopup-tab">
			<div v-for="( mapConfig, index) in mapConfigs" :key="mapConfig.id"
				:class="{ 'mappopup-tab-active': activeTab === index }">
				<button @click="() => { activeTab = index }">{{ activeTab === index ? mapConfig.title :
					(mapConfig.title.length > 5 ? mapConfig.title.slice(0, 4) + "..." : mapConfig.title) }}</button>
			</div>
		</div>
		<div class="mappopup-content">
			<div v-for="item in mapConfigs[activeTab].property" :key="item.key">
				<h3>{{ item.name }}</h3>
				<p>{{ popupContent[activeTab].properties[item.key] }}</p>
			</div>
		</div>
	</div>
</template>

<style lang="scss">
@keyframes easein {
	0% {
		opacity: 0
	}

	100% {
		opacity: 1
	}
}

.mapboxgl-popup {
	width: fit-content;
	min-width: 310px !important;
	animation: easein 0.2s linear;
}

.mapboxgl-popup-content {
	padding: 0 !important;
	border: solid 1px var(--color-border);
	box-shadow: 0px 0px 10px rgb(35, 35, 35) !important;
	border-radius: 5px !important;
	background-color: var(--color-component-background) !important;
}

.mapboxgl-popup-anchor-bottom .mapboxgl-popup-tip,
.mapboxgl-popup-anchor-bottom-left .mapboxgl-popup-tip,
.mapboxgl-popup-anchor-bottom-right .mapboxgl-popup-tip {
	border-top-color: var(--color-border) !important;
}

.mapboxgl-popup-anchor-top .mapboxgl-popup-tip,
.mapboxgl-popup-anchor-top-left .mapboxgl-popup-tip,
.mapboxgl-popup-anchor-top-right .mapboxgl-popup-tip {
	border-bottom-color: var(--color-border) !important;
}

.mapboxgl-popup-anchor-left .mapboxgl-popup-tip {
	border-right-color: var(--color-border) !important;
}

.mapboxgl-popup-anchor-right .mapboxgl-popup-tip {
	border-left-color: var(--color-border) !important;
}

.mapboxgl-popup-close-button {
	right: 15px !important;
	top: 10px !important;
	color: var(--color-complement-text);
	font-size: 1.2rem;
	line-height: 1rem;
}

.mappopup {
	max-height: 200px;
	padding: 10px;
	overflow-y: scroll;

	button {
		margin-bottom: 0.5rem;
		color: var(--color-complement-text);
	}

	&-tab {
		display: flex;
		margin-bottom: 0.5rem;

		button {
			margin: 0 4px 0 0;
			padding: 4px 4px;
			border-radius: 5px;
			background-color: rgb(77, 77, 77);
			opacity: 0.6;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			text-align: center;
			transition: color 0.2s, opacity 0.2s;
			user-select: none;

			&:hover {
				opacity: 0.8;
				color: white;
			}
		}

		&-active button {
			opacity: 1;
			color: white;
		}
	}

	&-content {
		width: fit-content;

		div {
			display: flex;
		}

		h3 {
			min-width: 100px;
		}

		p {
			text-align: justify;
		}
	}
}
</style>