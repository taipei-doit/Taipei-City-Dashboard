<script setup>
import { computed, onMounted, ref } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';
import { useAppStore } from '../store/appStore';

const { BASE_URL } = import.meta.env;
const props = defineProps(['docs', 'id']);
const appStore = useAppStore();

const doctext = ref('');
const sharedContent = ref({});

const parsedDoctext = computed(() => {
	const renderer = {
		blockquote(quote) {
			const no = quote[12] === '0' ? quote[13] : quote[12] + quote[13];
			quote = quote.replace("<pre>", "<pre class='inquote'>");

			if (quote[11] === "i") {
				quote = quote.slice(23);
				return `<blockquote class="info">
                    <h4>${appStore.lang === "en" ? "Information" : "資訊"} - ${no}</h4>
                    <p>${quote}
                    </blockquote>`;
			}
			else if (quote[11] === "w") {
				quote = quote.slice(23);
				return `<blockquote class="warning">
                    <h4>${appStore.lang === "en" ? "Warning" : "警告"} - ${no}</h4>
                    <p>${quote}
                    </blockquote>`;
			}
			else if (quote[11] === "t") {
				quote = quote.slice(23);
				return `<blockquote class="tip">
                    <h4>${appStore.lang === "en" ? "Tip" : "小撇步"} - ${no}</h4>
                    <p>${quote}
                    </blockquote>`;
			}
		},
		code(code, infostring) {
			const toBeCopied = code.replaceAll(`"`, `&quot;`);
			return `<pre><button class="${appStore.lang === 'en' ? '' : 'copy-ch'}" onclick="navigator.clipboard.writeText(\`${toBeCopied}\`)">content_paste</button><code class="language-${infostring}">${code}</code></pre>`;
		},
		codespan(code) {
			if (code === 'GET') {
				return `<code style="background-color: #6bdd9a; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'POST') {
				return `<code style="background-color: #fce47d; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'PATCH') {
				return `<code style="background-color: #c0a9e1; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'DEL') {
				return `<code style="background-color: #f7998e; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'DB') {
				return `<code style="background-color: #008bb9; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'PK') {
				return `<code style="background-color: gold; color: black; font-weight: bold">${code}</code>`;
			} else if (code === 'FK') {
				return `<code style="background-color: silver; color: black; font-weight: bold">${code}</code>`;
			}
			return `<code>${code}</code>`;
		},
		heading(text, level) {
			const parsedText = text.replaceAll('<em><strong>new', '<span>new').replaceAll('<strong><em>new', '<span>new').replaceAll('</strong></em>', '</span>').replaceAll('</em></strong>', '</span>');
			if (level >= 4) {
				return `<h${level}>${parsedText}</h${level}>`;
			}
			const headingId = parsedText.toLowerCase().replaceAll(' ', '-').replaceAll('<span>', '').replaceAll('</span>', '');
			return `<h${level} id="${headingId}">${parsedText} <a href="#${headingId}" class="hide-if-mobile">#</a></h${level}>`;
		},
		image(href, title, text) {
			return `<img src="${href.includes('http') ? '' : BASE_URL}${href}" alt="${text}" >`;
		},
		link(href, title, text) {
			if (href.startsWith('mailto:')) {
				return `<a href="${href}">${text}</a>`;
			}
			if (href.includes('http')) {
				return `<a href="${href}" target='_blank'>${text}</a>`;
			}
			return `<a href="${BASE_URL}${href}">${text}</a>`;
		},
		paragraph(text) {
			if (text.includes('<em>contributors</em>')) {
				const parsedContributors = text.replaceAll('<em>contributors</em>', '').replaceAll('<strong>', '<p>').replaceAll('</strong>', '</p>');
				return `<div class="docpagecontent-contributors">${parsedContributors}</div>`;
			}
			// replace <tpl> tag
			const tplRegex = /<tpl>(.*?)<\/tpl>/g;
			text = text.replace(tplRegex, (_, name) => {
				text += sharedContent.value[name] || '';
				return sharedContent.value[name] || '';
			});

			const parsedText = text.replaceAll('<em><strong>', '<span>').replaceAll('<strong><em>', '<span>').replaceAll('</strong></em>', '</span>').replaceAll('</em></strong>', '</span>');
			return `<p>${parsedText}</p>`;
		},
		table(header, body) {
			return `<div class="tablewrapper"><table>${header}${body}</table></div>`;
		},
	};
	marked.use({ renderer, mangle: false, headerIds: false });
	// eslint-disable-next-line no-misleading-character-class
	return marked.parse(doctext.value.replace(/^[\u200B\u200C\u200D\u200E\u200F\uFEFF]/, ""));
});

onMounted(async () => {
	// const module = await import(`../assets/articles/${props.docs}-${appStore.lang}/${props.id}.md`);
	// fetch(module.default).then(async res => {
	// 	return await res.text();
	// }).then(text => {
	// 	doctext.value = text;
	// 	setTimeout(() => {
	// 		hljs.highlightAll();
	// 	}, 50);
	// });

	// get template from common files
	const module = await import(`../assets/articles/${props.docs}-${appStore.lang}/${props.id}.md`);
	const mainContent = await fetch(module.default).then(res => res.text());
	const commonFiles = {
		ch: import.meta.glob('../assets/articles/common-ch/*.md'),
		en: import.meta.glob('../assets/articles/common-en/*.md'),
	}

	for (const [path, loader] of Object.entries(commonFiles[appStore.lang])) {
		const name = path.split('/').pop().replace('.md', '');
		const sharedText = await loader().then(res => fetch(res.default).then(res => res.text()));
		sharedContent.value[name] = marked.parse(sharedText);
	}
	
	doctext.value = mainContent;

	setTimeout(() => {
		hljs.highlightAll();
	}, 50);
})

</script>

<template>
	<div v-html="parsedDoctext" class="docpagecontent">
	</div>
</template>

<style lang="scss">
.docpagecontent {
	display: flex;
	flex-direction: column;
	overflow-y: visible;

	h2 {
		margin-top: 0.5rem;
		margin-bottom: 1.5rem;
		padding-top: 1.5rem;
		border-top: dashed 1px var(--color-border);
		font-size: var(--font-xl);
		text-align: justify;
	}

	h3 {
		font-size: var(--font-l);
		margin-bottom: 1.5rem;
		text-align: justify;
		font-weight: 400;
	}

	h2,
	h3 {
		display: flex;
		align-items: center;

		a {
			margin-left: 6px;
			opacity: 0;
			transition: opacity 0.2s;
			user-select: none;
		}

		&:hover a {
			opacity: 1;

			&:hover {
				opacity: 0.7;
			}
		}

		span {
			font-size: var(--font-m);
			background-color: rgb(213, 181, 0);
			padding: 1px 2px;
			margin-left: 6px;
			border-radius: 5px;
			font-weight: 700;
			user-select: none;
			pointer-events: none;
		}
	}

	p {
		font-size: var(--font-m);
		margin-bottom: 1.5rem;
		text-align: justify;

		span {
			font-family: var(--font-icon);
			vertical-align: text-top;
		}
	}

	a {
		color: var(--color-highlight);
		transition: opacity 0.2s;

		&:hover {
			opacity: 0.7;
		}
	}

	img {
		width: 90%;
		margin-left: 5%;
		border-radius: 5px;

		@media screen and (max-width: 850px) {
			width: 100%;
			margin-left: 0;
		}
	}

	code {
		font-family: var(--font-code);
		background-color: var(--color-component-background);
		padding: 2px 4px;
		border-radius: 5px;
		color: var(--color-normal-text);
		overflow-y: scroll;

		&::-webkit-scrollbar {
			height: 8px;
		}

		&::-webkit-scrollbar-thumb {
			background-color: var(--color-complement-text);
			border-radius: 8px;
		}

		&::-webkit-scrollbar-corner {
			background-color: var(--color-component-background);
		}
	}

	pre {
		position: relative;
		margin-bottom: 1.5rem;
		border-radius: 0.5rem;

		&.inquote {
			margin-top: 1.5rem;
			margin-bottom: 0;
		}

		button {
			position: absolute;
			display: flex;
			align-items: center;
			right: 0.5rem;
			top: 0.5rem;
			font-family: var(--font-icon);
			font-size: var(--font-l);
			color: var(--color-complement-text);
			transition: color 0.2s, font-size 0.2s;

			&::before {
				font-family: "微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans", "Helvetica";
				content: "Copied!";
				font-size: var(--font-s);
				margin: 4px 4px 0;
				opacity: 0;
				transition: opacity 0.2s;
				color: var(--color-normal-text);
			}

			&.copy-ch::before {
				content: "已複製！";
			}

			&:hover {
				color: var(--color-normal-text)
			}

			&:focus {
				font-size: 0;
				color: transparent;

				&::before {
					opacity: 1;
				}
			}
		}

		code,
		code span {
			font-family: var(--font-code) !important;
			background-color: var(--color-component-background) !important;
		}
	}

	blockquote {
		background-color: var(--color-border);
		margin-bottom: 1.5rem;
		padding: 1rem;
		border-radius: 5px;

		&.info {
			border-left: 5px solid var(--color-highlight);

			h4:before {
				content: "info_outline";
				font-family: var(--font-icon);
				margin-right: 6px;
				color: var(--color-highlight)
			}
		}

		&.warning {
			border-left: 5px solid rgb(227, 42, 42);

			h4:before {
				content: "warning_amber";
				font-family: var(--font-icon);
				margin-right: 6px;
				color: rgb(227, 42, 42)
			}
		}

		&.tip {
			border-left: 5px solid rgb(29, 187, 29);

			h4:before {
				content: "lightbulb_outline";
				font-family: var(--font-icon);
				margin-right: 6px;
				color: rgb(29, 187, 29)
			}
		}

		h4 {
			display: flex;
			align-items: flex-start;
			margin-bottom: 0.5rem;
		}

		p {
			margin-bottom: 0;
			margin-top: 1rem;
		}
	}

	.tablewrapper {
		border-top-left-radius: 5px;
		border-top-right-radius: 5px;
		overflow-x: scroll;
		margin-bottom: 1rem;

		table {
			width: max(800px, 100%);
			border-collapse: collapse;

			border-top-left-radius: 5px;
			border-top-right-radius: 5px;

			th,
			td {
				border: solid 1px var(--color-border);
				padding: 0.5rem;
				text-align: center;
			}

			th {
				background-color: var(--color-border);
			}

			td:first-child {
				width: 110px;
			}

			td:nth-child(2) {
				text-align: left;
			}
		}

		&::-webkit-scrollbar {
			height: 8px;
		}

		&::-webkit-scrollbar-thumb {
			background-color: var(--color-complement-text);
			border-radius: 8px;
		}

		&::-webkit-scrollbar-corner {
			background-color: var(--color-component-background);
		}
	}

	&-contributors {
		display: flex;
		flex-wrap: wrap;
		overflow: visible;
		margin-bottom: 24px;

		a {
			display: flex;
			align-items: center;
			justify-content: center;
			position: relative;
			overflow: visible;
			margin: 0.25rem 0.25rem 0 0;

			img {
				height: 3rem;
				width: 3rem;
				border: solid 1px var(--color-border);
				border-radius: 50%;
				margin: 0;
				transition: opacity 0.2s;

				&:hover+p {
					display: block;
					opacity: 1;
				}
			}

			p {
				display: none;
				position: absolute;
				top: -22px;
				margin: 0;
				padding: 2px 4px;
				border-radius: 4px;
				background-color: var(--color-border);
				opacity: 0;
				font-size: var(--font-s);
				text-wrap: nowrap;
				transition: opacity 0.2s;
			}

			&:hover {
				opacity: 1;
			}

			&:hover>img {
				opacity: 0.7;
			}
		}
	}
}
</style>
