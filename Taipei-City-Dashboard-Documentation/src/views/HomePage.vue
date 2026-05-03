<script setup>
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { DashboardComponent } from 'city-dashboard-component';
import { useAppStore } from '../store/appStore';

import { components } from '../assets/homepageComponents';
import { RouterLink } from 'vue-router';

const { t } = useI18n();
const appStore = useAppStore();

const currentImg = ref(0);
const lastImg = 6;

onMounted(() => {
	setInterval(() => {
		if (currentImg.value === lastImg) {
			return currentImg.value = 0;
		}
		currentImg.value += 1;
		return;
	}, 2800);
});
</script>

<template>
	<div class="homepage">
		<div class="homepage-positioner">
			<div class="homepage-header">
				<div class="homepage-header-title">
					<h1>{{ t('dashboard') }}</h1>
					<div :style="{ width: 'fit-content' }">
						<h2>{{ t('dashboard-tagline') }}</h2>
					</div>
					<div>
						<a :href="appStore.lang === 'en' ? 'https://www.youtube.com/watch?v=yTYEzTmoaoI' : 'https://www.youtube.com/watch?v=8MFc01e1P28'"
							target="_blank" rel="noreferrer"><button class="gray">{{ t('about-us')
								}}<span>play_circle</span></button></a><a
							href="https://github.com/taipei-doit/Taipei-City-Dashboard" target="_blank"
							rel="noreferrer"><button class="github">{{ t('github') }}<img
									src="../assets/images/github-mark.svg" /></button></a>
						<a href="https://citydashboard.taipei" target="_blank" rel="noreferrer"><button>{{
						t('platform')
					}}</button></a>
					</div>
				</div>
				<div class="homepage-header-image">
					<DashboardComponent :config="components[currentImg]" :footer="false"
						:style="{ width: '400px', height: '350px' }" :key="`component-${currentImg}`" />
				</div>
			</div>
			<hr />
			<div class="homepage-nav">
				<div class="homepage-nav-card">
					<h3>{{ t('front-end.name') }}{{ t('docs') }}</h3>
					<h4>{{ t('front-end.desc') }}</h4>
					<div>
						<router-link to="/front-end"><button>{{ t('get-started')
								}}<span>east</span></button></router-link>
					</div>
				</div>
				<div class="homepage-nav-card">
					<h3>{{ t('back-end.name') }}{{ t('docs') }}</h3>
					<h4>{{ t('back-end.desc') }}</h4>
					<div>
						<router-link to="/back-end"><button>{{ t('get-started')
								}}<span>east</span></button></router-link>
					</div>
				</div>
				<div class="homepage-nav-card">
					<h3>{{ t('data-end.name') }}{{ t('docs') }}</h3>
					<h4>{{ t('data-end.desc') }}</h4>
					<div>
						<router-link to="/data-end"><button>{{ t('get-started')
								}}<span>east</span></button></router-link>
					</div>
				</div>
			</div>
			<!-- <hr />
			<div class="homepage-utility">
				<h3>{{ t('more') }}</h3>
				<div class="homepage-nav">
					<router-link class="homepage-utility-card" to="/api">
						<h4>{{ t('api-tester.name') }}</h4>
						<span>arrow_circle_right</span>
					</router-link>
					<router-link class="homepage-utility-card" to="/component-registry">
						<h4>{{ t('component-registry.name') }}</h4>
						<span>arrow_circle_right</span>
					</router-link>
					<router-link class="homepage-utility-card" to="/" :style="{ opacity: 0.4 }">
						<h4>{{ t('data-pipeline-registry') }}</h4>
						<span>arrow_circle_right</span>
					</router-link>
				</div>
			</div> -->
			<br />
			<br />
			<br />
			<br />
			<!-- <hr />
			<div class="homepage-footer">
				<div></div>
			</div> -->
		</div>
	</div>
</template>

<style scoped lang="scss">
.homepage {
	display: flex;
	justify-content: center;
	width: 100%;
	height: calc(100vh - 60px);
	height: calc(var(--vh) * 100 - 60px);
	max-height: calc(100vh - 60px);
	max-height: calc(var(--vh) * 100 - 60px);
	overflow-y: scroll;

	@media screen and (max-width: 850px) {
		height: calc(100% - 60px);
	}

	&-positioner {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0 1rem;
		width: 100%;
		height: fit-content;

		@media screen and (min-width: 1200px) {
			width: 1200px
		}
	}

	hr {
		margin: 3rem 0;
		width: 100%;
		height: 0;
		border: none;
		border-top: 1px dashed var(--color-border);
	}

	&-header {
		display: grid;
		grid-template-columns: 3fr 400px;
		column-gap: 2rem;
		width: calc(100% - 3rem);
		margin-top: 3rem;
		padding-right: 3rem;

		@media screen and (max-width: 1000px) {
			grid-template-columns: 3fr 350px;
			margin-top: 1.5rem;
		}

		@media screen and (max-width: 900px) {
			width: 100%;
			grid-template-columns: 1fr;
			margin-top: 3rem;
			padding-right: 0;
		}

		&-title {
			display: flex;
			flex-direction: column;
			justify-content: center;
			align-items: center;


			h1 {
				font-size: 4rem;
				text-align: center;
				background: linear-gradient(75deg, var(--color-complement-text), var(--color-highlight) 70%, var(--color-complement-text), );
				background-clip: text;
				-webkit-background-clip: text;
				-webkit-text-fill-color: transparent;
				animation: title-gradient 10s linear none infinite;

				@media screen and (max-width: 550px) {
					font-size: 2.8rem;
				}
			}

			h2 {
				margin: 1rem auto 1.5rem;
				padding-right: 4px;
				border-right: .15em solid transparent;
				font-size: 1.8rem;
				font-weight: 400;
				text-align: center;
				color: #aeaeae;
				animation:
					typing 2.4s steps(40, end),
					blink-caret .8s step-end 8;
				overflow: hidden;
				white-space: nowrap;

				@media screen and (max-width: 550px) {
					font-size: 1.3rem;
					margin-top: 0.5rem;
				}
			}

			div {
				display: flex;
				justify-content: center;
			}
		}

		&-image {
			display: flex;
			justify-content: center;

			@media screen and (max-width: 1000px) {
				margin-top: 3rem;
			}
		}
	}


	&-nav {
		display: grid;
		grid-template-columns: 350px 350px 350px;
		column-gap: 1rem;
		padding: 0 1rem;

		@media screen and (max-width: 1200px) {
			grid-template-columns: 300px 300px 300px;
		}

		@media screen and (max-width: 1050px) {
			grid-template-columns: 280px 280px 280px;
		}

		@media screen and (max-width: 900px) {
			grid-template-columns: 500px;
			row-gap: 1rem;
		}

		@media screen and (max-width: 550px) {
			grid-template-columns: 320px;
		}

		&-card {
			display: flex;
			flex-direction: column;
			background-color: var(--color-component-background);
			border-radius: 5px;
			padding: var(--font-l);
			margin: 1rem 0;
			transition: box-shadow 0.2s;

			@media screen and (max-width: 900px) {
				margin: 0
			}

			&:hover {
				box-shadow: 0 0 5px var(--color-complement-text);
			}

			h3 {
				font-size: var(--font-xl);
			}

			p {
				font-size: 0.9rem;
				color: var(--color-complement-text)
			}

			h4 {
				margin: 1.5rem 0 2rem;
				font-size: var(--font-l);
				font-weight: 400;
			}

			div {
				flex: 1;
				display: flex;
				align-items: flex-end;
				justify-content: flex-end;
			}
		}
	}

	&-utility {
		h3 {
			text-align: center;
			font-size: var(--font-xl);
			margin-bottom: 2rem;
		}

		&-card {
			display: flex;
			align-items: center;
			background-color: var(--color-component-background);
			border-radius: 5px;
			padding: var(--font-l);
			transition: box-shadow 0.2s;
			margin: 4px 0;

			&:hover {
				box-shadow: 0 0 5px var(--color-complement-text);
				cursor: pointer;
			}

			h4 {
				font-size: var(--font-l);
				font-weight: 400;
			}

			span {
				margin-left: 8px !important;
				color: var(--color-normal-text) !important;
				font-size: var(--font-l);
			}
		}
	}

	span {
		margin-left: 4px;
		color: white;
		font-family: var(--font-icon);
	}

	button {
		display: flex;
		align-items: center;
		margin-left: 8px;
		padding: 6px;
		border-radius: 5px;
		background-color: var(--color-highlight);
		color: white;
		font-size: var(--font-m);
		transition: opacity 0.2s;

		&.gray {
			background-color: var(--color-complement-text);
		}

		&.github {
			border: 2px solid var(--color-normal-text);
			background-color: black;
			padding: 4px;
			color: white;

			img {
				margin-left: 4px;
				filter: invert(1);
				height: var(--font-m);
			}
		}

		&:hover {
			opacity: 0.7;
		}
	}
}

@keyframes fadeout {
	0% {
		opacity: 0;
	}

	5% {
		opacity: 0;
	}

	15% {
		opacity: 1;
	}

	75% {
		opacity: 1;
	}

	85% {
		opacity: 0;
	}

	100% {
		opacity: 0;
	}
}

@keyframes title-gradient {
	0% {
		background-position: 0;
	}

	50% {
		background-position: 600px;
	}

	100% {
		background-position: 0;
	}
}

@keyframes typing {
	from {
		width: 0
	}

	to {
		width: 100%
	}
}

@keyframes blink-caret {

	from,
	to {
		border-color: transparent
	}

	50% {
		border-color: var(--color-highlight);
	}
}
</style>