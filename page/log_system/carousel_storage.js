// carousel_storage.js - 轮播数据存储模块
(function(global) {
  const STORAGE_KEY = 'carouselConfig';

  function loadConfig() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.warn('读取配置失败', e);
      return [];
    }
  }

  function saveConfig(config) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  }

  global.CarouselStorage = {
    loadConfig,
    saveConfig
  };
})(window);
