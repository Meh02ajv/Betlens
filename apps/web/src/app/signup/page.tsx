"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/api";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(10, "Password must be at least 10 characters")
    .max(128, "Password too long"),
  is_adult_confirmed: z.boolean().refine((v) => v === true, {
    message: "You must confirm you are 18 or older",
  }),
});

type FormData = z.infer<typeof schema>;

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "10+ characters", ok: password.length >= 10 },
    { label: "Uppercase letter", ok: /[A-Z]/.test(password) },
    { label: "Number", ok: /\d/.test(password) },
    { label: "Special character", ok: /[^A-Za-z0-9]/.test(password) },
  ];
  const score = checks.filter((c) => c.ok).length;
  const colors = ["bg-live", "bg-live", "bg-yellow-400", "bg-positive", "bg-positive"];

  if (!password) return null;

  return (
    <div className="mt-2 space-y-1">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors ${i < score ? colors[score] : "bg-border"}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        {checks.map(({ label, ok }) => (
          <span
            key={label}
            className={`text-caption ${ok ? "text-positive" : "text-text-secondary"}`}
          >
            {ok ? "✓" : "○"} {label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function SignupPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const password = watch("password", "");

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await authApi.signup(data);
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sign up failed");
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-4">
        <div className="w-full max-w-sm card text-center space-y-4">
          <div className="w-12 h-12 bg-accent-tint rounded-full flex items-center justify-center mx-auto">
            <span className="text-accent text-section-title">✓</span>
          </div>
          <h2 className="text-section-title font-heading text-text-primary">Check your email</h2>
          <p className="text-body-sm text-text-secondary">
            We&apos;ve sent a verification link to your email address. Click it to activate your account.
          </p>
          <p className="text-caption text-text-secondary">
            (In development mode, your account is auto-verified. You can{" "}
            <Link href="/login" className="text-accent hover:underline">
              log in now
            </Link>
            .)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-accent rounded-button flex items-center justify-center">
              <span className="text-white font-heading">B</span>
            </div>
            <span className="text-page-title font-heading text-accent">BetLens</span>
          </Link>
          <p className="mt-2 text-body-sm text-text-secondary">Create your free account</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {error && (
              <div className="bg-red-50 border border-live text-live text-body-sm rounded-button px-3 py-2">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-body-sm font-label text-text-primary mb-1">
                Full name
              </label>
              <input id="name" type="text" autoComplete="name" className="input" {...register("name")} />
              {errors.name && <p className="mt-1 text-caption text-live">{errors.name.message}</p>}
            </div>

            <div>
              <label htmlFor="email" className="block text-body-sm font-label text-text-primary mb-1">
                Email
              </label>
              <input id="email" type="email" autoComplete="email" className="input" {...register("email")} />
              {errors.email && <p className="mt-1 text-caption text-live">{errors.email.message}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-body-sm font-label text-text-primary mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                className="input"
                {...register("password")}
              />
              <PasswordStrength password={password} />
              {errors.password && (
                <p className="mt-1 text-caption text-live">{errors.password.message}</p>
              )}
            </div>

            <div className="flex items-start gap-2">
              <input
                id="adult"
                type="checkbox"
                className="mt-0.5 w-4 h-4 accent-accent"
                {...register("is_adult_confirmed")}
              />
              <label htmlFor="adult" className="text-body-sm text-text-secondary">
                I confirm I am 18 years of age or older
              </label>
            </div>
            {errors.is_adult_confirmed && (
              <p className="text-caption text-live">{errors.is_adult_confirmed.message}</p>
            )}

            <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
              {isSubmitting ? "Creating account…" : "Create free account"}
            </button>
          </form>

          <p className="mt-4 text-center text-body-sm text-text-secondary">
            Already have an account?{" "}
            <Link href="/login" className="text-accent hover:underline font-label">
              Sign in
            </Link>
          </p>
        </div>

        <p className="mt-4 text-center text-caption text-text-secondary">
          By signing up you agree to our{" "}
          <Link href="/legal/terms" className="underline hover:text-accent">Terms</Link> and{" "}
          <Link href="/legal/privacy" className="underline hover:text-accent">Privacy Policy</Link>.
        </p>
      </div>
    </div>
  );
}