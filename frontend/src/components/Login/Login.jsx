import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { loginUser } from "../../features/user/userSlice";
import apiClient from "../../utils/apiClient";
import sessionCache from "../../utils/sessionCache";
import library_logo from "../../assets/library_logo_dark.png";

export default function Login() {
    const [localEmail, setLocalEmail] = useState("");
    const [localpassword, setLocalPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();
    const dispatch = useDispatch();

    // Check if user is already logged in using cache
    const cachedUser = sessionCache.getCachedUser();
    if (cachedUser && sessionCache.isValid()) {
        // User is already logged in, redirect to home
        navigate("/");
        return null;
    }

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!localEmail || !localpassword) {
            alert("Please enter both email and password");
            return;
        }

        setIsLoading(true);

        try {
            // Get nonce
            const nonceResponse = await apiClient.getJSON("/api/v1/nonce");
            const { nonce } = nonceResponse;

            // Login with device information
            const loginData = {
                email: localEmail,
                password: localpassword,
                nonce: nonce,
                device_id:
                    navigator.userAgent +
                    "_" +
                    screen.width +
                    "x" +
                    screen.height,
            };

            const response = await apiClient.postJSON(
                "/api/v1/login",
                loginData
            );

            if (response.user) {
                // Cache session data
                sessionCache.setSession({
                    user: response.user,
                    sessionId: response.session_id,
                    expiresAt: response.expires_at,
                    deviceId: loginData.device_id,
                });

                dispatch(
                    loginUser({
                        user_id: response.user.user_id,
                        firstname: response.user.first_name,
                        lastname: response.user.last_name,
                        is_admin: response.user.is_admin,
                    })
                );
                navigate("/books");
            } else {
                alert(
                    "Login successful but user data is missing. Please try again."
                );
            }
        } catch (error) {
            console.error("Login error:", error);
            alert(error.message || "Login failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/*
          This example requires updating your template:
  
          ```
          <html class="h-full bg-white">
          <body class="h-full">
          ```
        */}
            <div className="flex min-h-full flex-1">
                <div className="flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
                    <div className="mx-auto w-full max-w-sm lg:w-96">
                        <div>
                            <div className="flex items-center justify-center w-12 h-12 rounded-full border-2 border-gray-800">
                                <img
                                    alt="Library Logo"
                                    src={library_logo}
                                    className="h-8 w-auto"
                                />
                            </div>
                            <h2 className="mt-8 text-2xl/9 font-bold tracking-tight text-gray-900">
                                Sign in to your account
                            </h2>
                            <p className="mt-2 text-sm/6 text-gray-500">
                                Not a member?{" "}
                                <Link
                                    to="/register"
                                    className="font-semibold text-indigo-600 hover:text-indigo-500"
                                >
                                    Create a new account
                                </Link>
                            </p>
                        </div>

                        <div className="mt-10">
                            <div>
                                <form
                                    onSubmit={handleLogin}
                                    className="space-y-6"
                                >
                                    <div>
                                        <label
                                            htmlFor="email"
                                            className="block text-sm/6 font-medium text-gray-900"
                                        >
                                            Email address
                                        </label>
                                        <div className="mt-2">
                                            <input
                                                id="email"
                                                name="email"
                                                type="email"
                                                maxLength="50"
                                                required
                                                autoComplete="email"
                                                className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                                                value={localEmail}
                                                onChange={(e) =>
                                                    setLocalEmail(
                                                        e.target.value
                                                    )
                                                }
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label
                                            htmlFor="password"
                                            className="block text-sm/6 font-medium text-gray-900"
                                        >
                                            Password
                                        </label>
                                        <div className="mt-2">
                                            <input
                                                id="password"
                                                name="password"
                                                type="password"
                                                minLength="8"
                                                maxLength="50"
                                                required
                                                autoComplete="current-password"
                                                className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                                                value={localpassword}
                                                onChange={(e) =>
                                                    setLocalPassword(
                                                        e.target.value
                                                    )
                                                }
                                            />
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div className="flex gap-3">
                                            <div className="flex h-6 shrink-0 items-center">
                                                <div className="group grid size-4 grid-cols-1">
                                                    <input
                                                        id="remember-me"
                                                        name="remember-me"
                                                        type="checkbox"
                                                        className="col-start-1 row-start-1 appearance-none rounded border border-gray-300 bg-white checked:border-indigo-600 checked:bg-indigo-600 indeterminate:border-indigo-600 indeterminate:bg-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:border-gray-300 disabled:bg-gray-100 disabled:checked:bg-gray-100 forced-colors:appearance-auto"
                                                    />
                                                    <svg
                                                        fill="none"
                                                        viewBox="0 0 14 14"
                                                        className="pointer-events-none col-start-1 row-start-1 size-3.5 self-center justify-self-center stroke-white group-has-[:disabled]:stroke-gray-950/25"
                                                    >
                                                        <path
                                                            d="M3 8L6 11L11 3.5"
                                                            strokeWidth={2}
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                            className="opacity-0 group-has-[:checked]:opacity-100"
                                                        />
                                                        <path
                                                            d="M3 7H11"
                                                            strokeWidth={2}
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                            className="opacity-0 group-has-[:indeterminate]:opacity-100"
                                                        />
                                                    </svg>
                                                </div>
                                            </div>
                                            <label
                                                htmlFor="remember-me"
                                                className="block text-sm/6 text-gray-900"
                                            >
                                                Remember me
                                            </label>
                                        </div>

                                        <div className="text-sm/6">
                                            <a
                                                href="#"
                                                className="font-semibold text-indigo-600 hover:text-indigo-500"
                                            >
                                                Forgot password?
                                            </a>
                                        </div>
                                    </div>

                                    <div>
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:bg-indigo-400 disabled:cursor-not-allowed"
                                        >
                                            {isLoading
                                                ? "Signing in..."
                                                : "Sign in"}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="relative hidden w-0 flex-1 lg:block h-screen">
                    <img
                        alt=""
                        src="https://images.unsplash.com/photo-1496917756835-20cb06e75b4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1908&q=80"
                        className="absolute inset-0 size-full object-cover"
                    />
                </div>
            </div>
        </>
    );
}
