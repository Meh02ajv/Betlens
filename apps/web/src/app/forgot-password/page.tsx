"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/api";

const schema = z.object({ email: z.string().email("Enter a valid email") });
type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    await authApi.forgotPassword(data.email);
    setSent(true);
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-accent rounded-button flex items-center justify-center">
              <span className="text-white font-heading">B</span>
            </div>
            <span className="text-page-title font-heading text-accent">BetLens</span>
          </Link>
        </div>
        <div className="card">
          {sent ? (
            <div className="text-center space-y-3">
              <p className="text-section-title font-heading text-text-primary">Check your email</p>
              <p className="text-body-sm text-text-secondary">
                If that email is registered, a reset link has been sent. It expires in 30 minutes.
              </p>
              <Link href="/login" className="btn-primary block text-center">Back to login</Link>
            </div>
          ) : (
            <>
              <h1 className="text-section-title font-heading text-text-primary mb-1">Reset password</h1>
              <p className="text-body-sm text-text-secondary mb-4">
                Enter your email and we&apos;ll send a reset link.
              </p>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-body-sm font-label text-text-primary mb-1">Email</label>
                  <input id="email" type="email" className="input" {...register("email")} />
                  {errors.email && <p className="mt-1 text-caption text-live">{errors.email.message}</p>}
                </div>
                <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                  {isSubmitting ? "Sending…" : "Send reset link"}
                </button>
              </form>
              <p className="mt-4 text-center text-body-sm text-text-secondary">
                <Link href="/login" className="text-accent hover:underline">Back to login</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}