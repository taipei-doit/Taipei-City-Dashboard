export default {
  mounted(el) {
    const handler = (e) => {
      const canScrollHorizontally = el.scrollWidth > el.clientWidth;
      if (canScrollHorizontally && e.deltaY !== 0) {
        e.preventDefault();        // 只有能水平滾動才阻止垂直滾動
        el.scrollLeft += e.deltaY; // 垂直滾輪轉水平滾動
      }
      // 否則什麼都不做，垂直滾動自然生效
    };

    el.__horizontalWheelHandler__ = handler;
    el.addEventListener('wheel', handler, { passive: false });
  },

  unmounted(el) {
    const handler = el.__horizontalWheelHandler__;
    if (handler) {
      el.removeEventListener('wheel', handler);
      delete el.__horizontalWheelHandler__;
    }
  },
};
