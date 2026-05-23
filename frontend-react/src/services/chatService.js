import api from './api';

export const chatService = {

  async getConversations() {
    const response = await api.get('/chat/conversations');
    return response.data;
  },

 
  async getConversation(id) {
    const response = await api.get(`/chat/conversations/${id}`);
    return response.data;
  },

  
  async createConversation(title) {
    const response = await api.post('/chat/conversations', { title });
    return response.data;
  },

  
  async deleteConversation(id) {
    await api.delete(`/chat/conversations/${id}`);
  },

 
  async getMessages(conversationId) {
    const response = await api.get(`/chat/conversations/${conversationId}/messages`);
    return response.data;
  },


  async sendMessage(conversationId, message) {
    const response = await api.post(
        `/chat/conversations/${conversationId}/messages`, 
        { role: 'user', content: message }
    );
    return response.data;
},

  async addMessage(conversationId, role, content) {
    const response = await api.post(`/chat/conversations/${conversationId}/messages`, {
      role,
      content
    });
    return response.data;
  }
};
