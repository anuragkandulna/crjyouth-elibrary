import { Outlet } from "react-router-dom";
import { useRef, useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import Header from "./components/Header/Header";
import Footer from "./components/Footer/Footer";
import { loginUser } from "./features/user/userSlice";
import { getCurrentUser } from "./utils/authUtils";
import sessionManager from "./services/sessionManager";
import { store } from "./app/store";

// <Header> <Outlet> <Footer>
// Basic Layout of App
function App() {
    const headerRef = useRef(null);
    const [headerHeight, setHeaderHeight] = useState(0);
    const dispatch = useDispatch();

    useEffect(() => {
        if (headerRef.current) {
            setHeaderHeight(headerRef.current.offsetHeight);
        }
    }, []);

    // Check authentication status on app load
    useEffect(() => {
        const checkAuth = async () => {
            try {
                const user = await getCurrentUser();
                if (user) {
                    dispatch(
                        loginUser({
                            user_id: user.user_id,
                            firstname: user.first_name,
                            lastname: user.last_name,
                            is_admin: user.is_admin,
                        })
                    );
                }
            } catch (error) {
                console.error("Failed to check authentication:", error);
            }
        };
        checkAuth();
    }, [dispatch]);

    // Expose store globally for session manager
    useEffect(() => {
        window.store = store;
        return () => {
            delete window.store;
        };
    }, []);

    return (
        <>
            <div className="bg-white">
                <header
                    ref={headerRef}
                    className="absolute inset-x-0 top-0 z-50"
                >
                    <Header />
                </header>

                <main style={{ paddingTop: headerHeight }}>
                    <Outlet />
                </main>
                <Footer />
            </div>
        </>
    );
}

export default App;
