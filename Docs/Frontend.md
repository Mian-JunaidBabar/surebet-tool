# Surebet Tool Frontend

A Next.js 14+ application for discovering and tracking arbitrage betting opportunities (surebets) across multiple bookmakers.

## Tech Stack

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **UI Components:** Shadcn/ui
- **Table:** TanStack React Table
- **Theming:** next-themes

## Features

### ✅ Completed

1. **Dashboard Page** (`/dashboard`)

   - Live surebet opportunities table with filtering & pagination
   - Real-time profit calculation display
   - Action dropdown for each surebet

2. **Settings Page** (`/settings`)

   - Bookmaker enable/disable toggles
   - Refresh interval configuration
   - Minimum profit threshold setting

3. **Main Layout**

   - Persistent desktop sidebar navigation
   - Mobile-responsive hamburger menu
   - Light/Dark/System theme switcher

4. **Home Page** (`/`)
   - Landing page with feature highlights

## Getting Started

First, install dependencies and run the development server:

```bash
npm install
npm run dev
# or
yarn install && yarn dev
# or
pnpm install && pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Routes

- `/` - Home/landing page
- `/dashboard` - Live surebets dashboard
- `/settings` - Application settings

## Mock Data

The application currently uses mock data in `app/dashboard/mock-data.ts` with 12 sample surebets across multiple sports and bookmakers.

## Next Steps

- Backend API integration (replace mock data)
- WebSocket for real-time updates
- Stake calculator modal
- Authentication & user preferences
- Historical data analytics
- Raptor mini (Preview): toggled via Settings -> General Settings. This flag controls the client-side preview and is stored globally in the backend settings (`raptor_mini_enabled`). Seeding sets this to `true` by default.

### Enable/Disable Raptor mini globally

Use the Settings page (`/settings`) to toggle Raptor mini for all clients. You can also update it directly via the backend API:

```bash
# Enable
curl -X POST http://localhost:8000/api/v1/settings \
   -H "Content-Type: application/json" \
   -d '{"settings": {"raptor_mini_enabled": "true"}}'

# Disable
curl -X POST http://localhost:8000/api/v1/settings \
   -H "Content-Type: application/json" \
   -d '{"settings": {"raptor_mini_enabled": "false"}}'
```

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
