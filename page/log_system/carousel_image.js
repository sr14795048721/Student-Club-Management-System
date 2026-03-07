// carousel_image.js - 轮播图片处理模块
(function(global) {
  const IMG_BASE_PATH = '/image/log.image/';
  const IMG_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'];

  async function scanImages() {
    const images = [];
    
    for (let i = 1; i <= 20; i++) {
      const name = 'slide' + i;
      for (const ext of IMG_EXTENSIONS) {
        const path = IMG_BASE_PATH + name + ext;
        try {
          const exists = await checkImageExists(path);
          if (exists) {
            images.push({ name, path });
            break;
          }
        } catch (e) {}
      }
    }
    return images;
  }

  function checkImageExists(path) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = path;
    });
  }

  function getImagePath(name) {
    if (!name) return Promise.resolve(IMG_BASE_PATH + 'slide1.png');
    return new Promise((resolve) => {
      let found = false;
      let checked = 0;
      
      IMG_EXTENSIONS.forEach(ext => {
        const img = new Image();
        const path = IMG_BASE_PATH + name + ext;
        
        img.onload = () => {
          if (!found) {
            found = true;
            resolve(path);
          }
        };
        
        img.onerror = () => {
          checked++;
          if (checked === IMG_EXTENSIONS.length && !found) {
            resolve(IMG_BASE_PATH + name + '.jpg');
          }
        };
        
        img.src = path;
      });
    });
  }

  global.CarouselImage = {
    IMG_BASE_PATH,
    scanImages,
    getImagePath
  };
})(window);
