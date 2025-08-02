import { Outlet } from "react-router-dom";
import { useRef, useEffect, useState } from "react";
import Header from "./components/Header/Header";
import Footer from "./components/Footer/Footer";

// <Header> <Outlet> <Footer>
// Basic Layout of App
function App() {
    const headerRef = useRef(null);
    const [headerHeight, setHeaderHeight] = useState(0);

    useEffect(() => {
        if (headerRef.current) {
            setHeaderHeight(headerRef.current.offsetHeight);
        }
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
