export interface Classification {
  id: number;
  image_url: string;
  waste_type: string;
  confidence: string;
  description: string;
  possible_uses: string[];
  status: "pending_review" | "confirmed";
  created_at: string;
}