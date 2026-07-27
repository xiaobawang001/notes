export interface TokenResponse {
  token: string
  token_type: string
  user_id: number
  username: string
  role: string
}

export interface LoginUser {
  id: number
  username: string
  role: string
}
