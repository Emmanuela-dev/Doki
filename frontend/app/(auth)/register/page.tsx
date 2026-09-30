import { AuthShell } from "@/components/auth/AuthShell";
import { RegisterForm } from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <AuthShell
      image="https://images.unsplash.com/photo-1624668430039-0175a0fbf006?q=80&w=1600&auto=format&fit=crop"
      imageAlt="A harvest basket filled with fresh tomatoes and vegetables"
      quote="Turning organic waste into value."
    >
      <RegisterForm />
    </AuthShell>
  );
}