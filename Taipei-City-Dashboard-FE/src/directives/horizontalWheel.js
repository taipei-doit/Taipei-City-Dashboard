export default {
	mounted(el) {
		const handler = (e) => {
			if (e.deltaY !== 0) {
				e.preventDefault()
				el.scrollLeft += e.deltaY
			}
		}
		el.__horizontalWheelHandler__ = handler
		el.addEventListener('wheel', handler, { passive: false })
	},
	unmounted(el) {
		const handler = el.__horizontalWheelHandler__
		if (handler) {
			el.removeEventListener('wheel', handler)
			delete el.__horizontalWheelHandler__
		}
	},
}
