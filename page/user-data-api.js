// 用户数据管理 API 客户端
class UserDataAPI {
  constructor() {
    this.token = localStorage.getItem('authToken');
    this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  }

  // 获取用户资料
  async getProfile(userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/data?type=profile`, {
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 保存用户资料
  async saveProfile(data, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/data?type=profile`, {
      method: 'POST',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return await res.json();
  }

  // 获取用户社团列表
  async getClubs(userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/clubs`, {
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 创建社团
  async createClub(clubData, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/clubs`, {
      method: 'POST',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(clubData)
    });
    return await res.json();
  }

  // 更新社团
  async updateClub(clubId, clubData, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/clubs?id=${clubId}`, {
      method: 'PUT',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(clubData)
    });
    return await res.json();
  }

  // 删除社团
  async deleteClub(clubId, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/clubs?id=${clubId}`, {
      method: 'DELETE',
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 获取用户活动列表
  async getActivities(userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/activities`, {
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 创建活动
  async createActivity(activityData, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/activities`, {
      method: 'POST',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(activityData)
    });
    return await res.json();
  }

  // 更新活动
  async updateActivity(activityId, activityData, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/activities?id=${activityId}`, {
      method: 'PUT',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(activityData)
    });
    return await res.json();
  }

  // 删除活动
  async deleteActivity(activityId, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/activities?id=${activityId}`, {
      method: 'DELETE',
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 获取自定义数据
  async getCustomData(type, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/data?type=${type}`, {
      headers: { 'Authorization': this.token }
    });
    return await res.json();
  }

  // 保存自定义数据
  async saveCustomData(type, data, userId = null) {
    const id = userId || this.userInfo.id;
    const res = await fetch(`/api/user/${id}/data?type=${type}`, {
      method: 'POST',
      headers: {
        'Authorization': this.token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return await res.json();
  }
}

// 导出实例
const userDataAPI = new UserDataAPI();
