import { useState, useEffect, useRef } from "react";
import {
    Bars3Icon,
    XMarkIcon,
    UserIcon,
    ChevronDownIcon,
} from "@heroicons/react/24/outline";
import { Dialog, DialogPanel } from "@headlessui/react";
import { Link, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { logoutUser } from "../../features/user/userSlice";
import sessionManager from "../../services/sessionManager";
import sessionCache from "../../utils/sessionCache";

// # 1. Admin Dashboard -> Private route only for admin
// # 2. Books -> Public route
// # 3. Library Card -> Public route

const navigation = [
    { name: "Books", href: "/books" },
    { name: "Library Card", href: "/library-card" },
];

export default function Header() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userDropdownOpen, setUserDropdownOpen] = useState(false);
    const navigate = useNavigate();
    const dispatch = useDispatch();
    const { user_id, firstname, lastname } = useSelector((state) => state.user);
    const dropdownRef = useRef(null);

    // Check if user is logged in (has user_id)
    const isLoggedIn = !!user_id;
    const fullName = `${firstname} ${lastname}`.trim();

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target)
            ) {
                setUserDropdownOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const handleLogout = async () => {
        try {
            // Clear session cache first
            sessionCache.clear();

            const response = await fetch(
                "http://localhost:5001/api/v1/logout",
                {
                    method: "POST",
                    credentials: "include",
                }
            );
            if (response.ok) {
                dispatch(logoutUser());
                navigate("/");
            } else {
                // Even if logout fails, clear local state
                sessionCache.clear();
                dispatch(logoutUser());
                navigate("/");
            }
        } catch (error) {
            console.error("Logout error:", error);
            // Even if logout fails, clear local state
            sessionCache.clear();
            dispatch(logoutUser());
            navigate("/");
        }
    };

    const handleLogoutAll = async () => {
        try {
            // Clear session cache first
            sessionCache.clear();

            const success = await sessionManager.logoutAllSessions();
            if (success) {
                dispatch(logoutUser());
                navigate("/");
            } else {
                // Even if logout fails, clear local state
                sessionCache.clear();
                dispatch(logoutUser());
                navigate("/");
            }
        } catch (error) {
            console.error("Logout all error:", error);
            // Even if logout fails, clear local state
            sessionCache.clear();
            dispatch(logoutUser());
            navigate("/");
        }
    };

    const handleProfileClick = () => {
        navigate("/profile");
        setUserDropdownOpen(false);
    };

    return (
        <>
            <nav
                aria-label="Global"
                className="flex items-center justify-between p-6 lg:px-8 bg-gray-900"
            >
                <div className="flex lg:flex-1">
                    <Link href="#" className="-m-1.5 p-1.5">
                        <span className="sr-only">Your Company</span>
                        <img
                            alt=""
                            src="https://tailwindui.com/plus/img/logos/mark.svg?color=indigo&shade=500"
                            className="h-8 w-auto"
                        />
                    </Link>
                </div>
                <div className="flex lg:hidden">
                    <button
                        type="button"
                        onClick={() => setMobileMenuOpen(true)}
                        className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-400"
                    >
                        <span className="sr-only">Open main menu</span>
                        <Bars3Icon aria-hidden="true" className="size-6" />
                    </button>
                </div>
                <div className="hidden lg:flex lg:gap-x-12">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            to={item.href}
                            className="text-sm/6 font-semibold text-white"
                        >
                            {item.name}
                        </Link>
                    ))}
                </div>
                <div className="hidden lg:flex lg:flex-1 lg:justify-end">
                    {isLoggedIn ? (
                        // Logged in state - Profile image + name with dropdown
                        <div className="relative" ref={dropdownRef}>
                            <button
                                onClick={() =>
                                    setUserDropdownOpen(!userDropdownOpen)
                                }
                                className="flex items-center gap-2 text-sm/6 font-semibold text-white hover:text-gray-300 transition-colors"
                            >
                                <img
                                    alt={fullName}
                                    src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
                                    className="size-8 rounded-full bg-gray-800 outline outline-1 -outline-offset-1 outline-white/10"
                                />
                                <span>{fullName}</span>
                                <ChevronDownIcon className="size-4" />
                            </button>

                            {/* Dropdown Menu */}
                            {userDropdownOpen && (
                                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                                    <button
                                        onClick={handleProfileClick}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    >
                                        Profile
                                    </button>
                                    <button
                                        onClick={handleLogout}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    >
                                        Logout
                                    </button>
                                    <button
                                        onClick={handleLogoutAll}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-t border-gray-100"
                                    >
                                        Logout All
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        // Logged out state - Profile icon + "Log In" text
                        <Link
                            to="/login"
                            className="flex items-center gap-2 text-sm/6 font-semibold text-white hover:text-gray-300 transition-colors"
                        >
                            <UserIcon className="size-6" />
                            <span>Log In</span>
                        </Link>
                    )}
                </div>
            </nav>
            <Dialog
                open={mobileMenuOpen}
                onClose={setMobileMenuOpen}
                className="lg:hidden"
            >
                <div className="fixed inset-0 z-50" />
                <DialogPanel className="fixed inset-y-0 right-0 z-50 w-full overflow-y-auto bg-gray-900 px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-white/10">
                    <div className="flex items-center justify-between">
                        <Link to="/" className="-m-1.5 p-1.5">
                            <span className="sr-only">Your Company</span>
                            <img
                                alt=""
                                src="https://tailwindui.com/plus/img/logos/mark.svg?color=indigo&shade=500"
                                className="h-8 w-auto"
                            />
                        </Link>
                        <button
                            type="button"
                            onClick={() => setMobileMenuOpen(false)}
                            className="-m-2.5 rounded-md p-2.5 text-gray-400"
                        >
                            <span className="sr-only">Close menu</span>
                            <XMarkIcon aria-hidden="true" className="size-6" />
                        </button>
                    </div>
                    <div className="mt-6 flow-root">
                        <div className="-my-6 divide-y divide-gray-500/25">
                            <div className="space-y-2 py-6">
                                {navigation.map((item) => (
                                    <Link
                                        key={item.name}
                                        to={item.href}
                                        className="-mx-3 block rounded-lg px-3 py-2 text-base/7 font-semibold text-white hover:bg-gray-800"
                                    >
                                        {item.name}
                                    </Link>
                                ))}
                            </div>
                            <div className="lg:hidden">
                                <div className="px-2 pt-2 pb-3 space-y-1">
                                    {isLoggedIn ? (
                                        <>
                                            <div className="px-3 py-2 text-sm text-gray-300">
                                                Welcome, {fullName}
                                            </div>
                                            <Link
                                                to="/profile"
                                                className="block px-3 py-2 text-base font-medium text-white hover:text-gray-300 hover:bg-gray-700 rounded-md"
                                            >
                                                Profile
                                            </Link>
                                            <button
                                                onClick={handleLogout}
                                                className="block w-full text-left px-3 py-2 text-base font-medium text-white hover:text-gray-300 hover:bg-gray-700 rounded-md"
                                            >
                                                Logout
                                            </button>
                                            <button
                                                onClick={handleLogoutAll}
                                                className="block w-full text-left px-3 py-2 text-base font-medium text-white hover:text-gray-300 hover:bg-gray-700 rounded-md border-t border-gray-600"
                                            >
                                                Logout All
                                            </button>
                                        </>
                                    ) : (
                                        <Link
                                            to="/login"
                                            className="block px-3 py-2 text-base font-medium text-white hover:text-gray-300 hover:bg-gray-700 rounded-md"
                                        >
                                            Login
                                        </Link>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </DialogPanel>
            </Dialog>
        </>
    );
}
