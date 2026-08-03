export type ChannelType = string;

export interface Message {
  id: string;
  conversation_id: string;
  sender: 'user' | 'bot';
  message: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  platform: ChannelType;
  created_at: string;
  messages?: Message[];
}
