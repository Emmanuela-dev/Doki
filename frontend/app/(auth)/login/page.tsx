import { AuthShell } from "@/components/auth/AuthShell";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <AuthShell
      image="https://images.unsplash.com/photo-1633412954800-b2a39586e3b6?q=80&w=1600&auto=format&fit=crop"
      imageAlt="Sorted waste material ready for processing"
      quote="Point. Snap. List. Connect. Trade. Reuse."
    >
      <LoginForm />
    </AuthShell>
  );
}