export default {
	mounted(el) {
		// 滑鼠滾輪（桌機）
		const wheelHandler = (e) => {
			const canScrollHorizontally = el.scrollWidth > el.clientWidth;
			if (canScrollHorizontally && e.deltaY !== 0) {
				e.preventDefault();
				el.scrollLeft += e.deltaY;
			}
		};

		// 觸控（手機）
		let startX = 0;
		let startY = 0;

		const touchStartHandler = (e) => {
			startX = e.touches[0].clientX;
			startY = e.touches[0].clientY;
		};

		const touchMoveHandler = (e) => {
			const canScrollHorizontally = el.scrollWidth > el.clientWidth;
			if (!canScrollHorizontally) return;

			const dx = startX - e.touches[0].clientX;
			const dy = startY - e.touches[0].clientY;

			// 水平滑動幅度大於垂直才攔截
			if (Math.abs(dx) > Math.abs(dy)) {
				e.preventDefault();
				el.scrollLeft += dx;
				startX = e.touches[0].clientX;
			}
		};

		el.__horizontalWheelHandler__ = wheelHandler;
		el.__touchStartHandler__ = touchStartHandler;
		el.__touchMoveHandler__ = touchMoveHandler;

		el.addEventListener("wheel", wheelHandler, { passive: false });
		el.addEventListener("touchstart", touchStartHandler, { passive: true });
		el.addEventListener("touchmove", touchMoveHandler, { passive: false });
	},

	unmounted(el) {
		el.removeEventListener("wheel", el.__horizontalWheelHandler__);
		el.removeEventListener("touchstart", el.__touchStartHandler__);
		el.removeEventListener("touchmove", el.__touchMoveHandler__);
		delete el.__horizontalWheelHandler__;
		delete el.__touchStartHandler__;
		delete el.__touchMoveHandler__;
	},
};