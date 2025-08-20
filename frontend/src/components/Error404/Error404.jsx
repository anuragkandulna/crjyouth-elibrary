import { Link } from "react-router-dom";

export default function Error404() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="text-center max-w-md">
                <div className="text-8xl font-bold text-indigo-600 mb-4">
                    404
                </div>
                <h1 className="text-2xl font-semibold text-gray-900 mb-3">
                    Page not found
                </h1>
                <p className="text-gray-600 mb-8">
                    The page you're looking for doesn't exist.
                </p>
                <Link
                    to="/"
                    className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-500 transition-colors"
                >
                    Go back home
                </Link>
            </div>
        </div>
    );
}
