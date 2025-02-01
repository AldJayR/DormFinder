import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";
import type { Route } from "./+types/root";
import stylesheet from "./app.css?url";
import { AuthProvider } from "./contexts/AuthContext";


export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
  { rel: "stylesheet", href: stylesheet },
  { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404 | Page Not Found" : "Application Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : "Please try again later.";
  } else if (error instanceof Error) {
    details = import.meta.env.DEV ? error.message : "Unexpected error occurred";
    stack = import.meta.env.DEV ? error.stack : undefined;
  }

  // Security: Never expose stack traces in production
  if (!import.meta.env.DEV) {
    stack = undefined;
    details = "An unexpected error occurred. Our team has been notified.";
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1 className="text-2xl font-bold text-red-600">{message}</h1>
      <p className="text-gray-600 mt-2">{details}</p>
      {stack && (
        <pre className="w-full p-4 overflow-x-auto bg-gray-100 mt-4 rounded">
          <code className="text-sm">{stack}</code>
        </pre>
      )}
    </main>
  );
}