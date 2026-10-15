"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/api";
import { login } from "@/lib/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      const tokens = await authApi.login(data.email, data.password);
      login(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-accent rounded-button flex items-center justify-center">
              <span className="text-white font-heading">B</span>
            </div>
            <span className="text-page-title font-heading text-accent">BetLens</span>
          </Link>
          <p className="mt-2 text-body-sm text-text-secondary">
            Sign in to your account
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {error && (
              <div className="bg-red-50 border border-live text-live text-body-sm rounded-button px-3 py-2">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-body-sm font-label text-text-primary mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="input"
                {...register("email")}
              />
              {errors.email && (
                <p className="mt-1 text-caption text-live">{errors.email.message}</p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="block text-body-sm font-label text-text-primary">
                  Password
                </label>
                <Link href="/forgot-password" className="text-caption text-accent hover:underline">
                  Forgot password?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className="input"
                {...register("password")}
              />
              {errors.password && (
                <p className="mt-1 text-caption text-live">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full"
            >
              {isSubmitting ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-4 text-center text-body-sm text-text-secondary">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-accent hover:underline font-label">
              Create one free
            </Link>
          </p>
        </div>

        <p className="mt-6 text-center text-caption text-text-secondary">
          Demo account: demo@betlens.com / demo123456
        </p>
      </div>
    </div>
  );
}