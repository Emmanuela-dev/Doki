export type UserRole = "SELLER" | "BUYER";

export interface RegisterPayload {
  full_name: string;
  business_name: string;
  email: string;
  phone: string;
  password: string;
  role: UserRole;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserOut {
  id: number;
  full_name: string;
  business_name: string;
  email: string;
  phone: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}