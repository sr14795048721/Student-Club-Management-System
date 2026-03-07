// log_image_system.js - 轮播系统统一接口（兼容旧代码）
(function(global) {
  global.CarouselSystem = {
    STORAGE_KEY: 'carouselConfig',
    IMG_BASE_PATH: '/image/log.image/',
    loadConfig: () => global.CarouselStorage.loadConfig(),
    saveConfig: (config) => global.CarouselStorage.saveConfig(config),
    getImagePath: (name) => global.CarouselImage.getImagePath(name),
    scanImages: () => global.CarouselImage.scanImages()
  };
})(window);
