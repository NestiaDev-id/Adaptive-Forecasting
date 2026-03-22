/**
 * Centralized API base URL resolution.
 *
 * - Development: `VITE_API_URL` defaults to `""` so requests go to relative `/api/...`
 *   paths, which are proxied to `http://localhost:8000` by the Vite dev server.
 * - Production: `VITE_API_URL` **must** be set to the deployed backend URL
 *   (e.g. `https://adaptive-forecasting-backend.vercel.app`) at build time.
 *   If it is missing in a production build a console error is emitted here, and
 *   a visible toast warning is shown by the root `App` component.
 */

export const BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

if (import.meta.env.PROD && !BASE_URL) {
  console.error(
    "[Adaptive Forecasting] VITE_API_URL is not set. " +
      "All API calls will fail in production. " +
      "Set VITE_API_URL to your backend URL in your hosting provider's environment variables " +
      "(e.g. https://adaptive-forecasting-backend.vercel.app)."
  );
}
