import { Outlet } from "react-router-dom";
import { useRef, useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import Header from "./components/Header/Header";
import Footer from "./components/Footer/Footer";
import { loginUser } from "./features/user/userSlice";
import sessionCache from "./utils/sessionCache";
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

    // Check authentication status using cache
    useEffect(() => {
        const cachedUser = sessionCache.getCachedUser();
        if (cachedUser && sessionCache.isValid()) {
            dispatch(
                loginUser({
                    user_id: cachedUser.user_id,
                    firstname: cachedUser.first_name,
                    lastname: cachedUser.last_name,
                    is_admin: cachedUser.is_admin,
                })
            );
        }
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
