/**
 * Store global Zustand pour OW Coach.
 * Gère : utilisateur, héros chargés, filtres actifs, mode overlay.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

const useAppStore = create(
  persist(
    (set, get) => ({
      // ─── Auth ──────────────────────────────────────────────────────────────
      user: null,      // { username, email, token }
      setUser: (user) => {
        set({ user });
        if (user?.token) localStorage.setItem("ow_token", user.token);
        else localStorage.removeItem("ow_token");
      },
      logout: () => {
        set({ user: null });
        localStorage.removeItem("ow_token");
      },

      // ─── Héros (cache local) ───────────────────────────────────────────────
      heroes: [],
      setHeroes: (heroes) => set({ heroes }),

      // ─── Filtres TierList / CounterPicker ──────────────────────────────────
      filters: {
        role:  null,   // "tank" | "dps" | "support" | null
        tier:  null,   // "S" | "A" | ... | null
        style: null,   // "brawl" | "dive" | "poke" | null
      },
      setFilter: (key, value) =>
        set((s) => ({ filters: { ...s.filters, [key]: value } })),
      resetFilters: () =>
        set({ filters: { role: null, tier: null, style: null } }),

      // ─── Mode overlay ──────────────────────────────────────────────────────
      overlayMode: false,
      toggleOverlay: () => set((s) => ({ overlayMode: !s.overlayMode })),
    }),
    {
      name: "ow-coach-store",
      // Ne persiste que l'utilisateur — les héros sont rechargés au démarrage
      partialize: (state) => ({ user: state.user }),
    }
  )
);

export default useAppStore;
