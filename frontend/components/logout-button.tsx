"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [carregando, setCarregando] = useState(false);

  async function handleLogout() {
    setCarregando(true);
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
      router.push("/login");
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <button
      onClick={handleLogout}
      disabled={carregando}
      className="rounded border border-neutral-300 px-3 py-1 text-sm hover:bg-neutral-100 disabled:opacity-50"
    >
      {carregando ? "Saindo…" : "Sair"}
    </button>
  );
}
