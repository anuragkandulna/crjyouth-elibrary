import { Link } from "react-router-dom";
import library_room from "../../assets/room.jpg";
import img1 from "../../assets/1.jpg";
import img2 from "../../assets/2.jpg";
import img3 from "../../assets/3.jpg";
import img4 from "../../assets/4.jpg";
import img5 from "../../assets/5.jpg";
import img6 from "../../assets/6.jpg";
import img7 from "../../assets/7.jpg";
import img8 from "../../assets/8.jpg";
import img9 from "../../assets/9.jpg";
import img10 from "../../assets/10.jpg";

const favorites = [
    {
        id: 1,
        name: "Collins Gem Bible Guide",
        author: "Collins Gem",
        language: "English",
        href: "#",
        imageSrc: img8,
        imageAlt: "",
    },
    {
        id: 2,
        name: "The Diary of Samuel Pepys",
        author: "R.C. Latham",
        language: "English",
        href: "#",
        imageSrc: img9,
        imageAlt: "",
    },
    {
        id: 3,
        name: "Buttery Kisses",
        author: "Bob Carlisle",
        language: "English",
        href: "#",
        imageSrc: img10,
        imageAlt: "",
    },
];

export default function Home() {
    return (
        <>
            <section>
                {/* Hero section */}
                <div className="pb-80 pt-16 sm:pb-40 sm:pt-24 lg:pb-48 lg:pt-40">
                    <div className="relative mx-auto max-w-7xl px-4 sm:static sm:px-6 lg:px-8">
                        <div className="sm:max-w-lg">
                            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
                                Check out our new arrivals
                            </h1>
                            <p className="mt-4 text-xl text-gray-500">
                                Our new arrivals are here to help you find the
                                perfect book.
                            </p>
                        </div>
                        <div>
                            <div className="mt-10">
                                {/* Decorative image grid */}
                                <div
                                    aria-hidden="true"
                                    className="pointer-events-none lg:absolute lg:inset-y-0 lg:mx-auto lg:w-full lg:max-w-7xl"
                                >
                                    <div className="absolute transform sm:left-1/2 sm:top-0 sm:translate-x-8 lg:left-1/2 lg:top-1/2 lg:-translate-y-1/2 lg:translate-x-8">
                                        <div className="flex items-center space-x-6 lg:space-x-8">
                                            <div className="grid shrink-0 grid-cols-1 gap-y-6 lg:gap-y-8">
                                                <div className="h-64 w-44 overflow-hidden rounded-lg sm:opacity-0 lg:opacity-100 border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img1}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img2}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                            </div>
                                            <div className="grid shrink-0 grid-cols-1 gap-y-6 lg:gap-y-8">
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img3}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img4}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img5}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                            </div>
                                            <div className="grid shrink-0 grid-cols-1 gap-y-6 lg:gap-y-8">
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img6}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                                <div className="h-64 w-44 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                                                    <img
                                                        alt=""
                                                        src={img7}
                                                        className="size-full object-cover"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <Link
                                    to="/books"
                                    className="inline-block rounded-md border border-transparent bg-indigo-600 px-8 py-3 text-center font-medium text-white hover:bg-indigo-700"
                                >
                                    Browse Collection
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Featured section */}
            <section aria-labelledby="cause-heading">
                <div className="relative bg-gray-800 px-6 py-32 sm:px-12 sm:py-40 lg:px-16">
                    <div className="absolute inset-0 overflow-hidden">
                        <img
                            alt=""
                            src={library_room}
                            className="size-full object-cover"
                        />
                    </div>
                    <div
                        aria-hidden="true"
                        className="absolute inset-0 bg-gray-900/50"
                    />
                    <div className="relative mx-auto flex max-w-3xl flex-col items-center text-center">
                        <h2
                            id="cause-heading"
                            className="text-3xl font-bold tracking-tight text-white sm:text-4xl"
                        >
                            Our Mission
                        </h2>
                        <p className="mt-3 text-xl text-white">
                            Our mission is to provide a space for learning and
                            discovery.
                        </p>
                        <Link
                            to="/about"
                            className="mt-8 block w-full rounded-md border border-transparent bg-white px-8 py-3 text-base font-medium text-gray-900 hover:bg-gray-100 sm:w-auto"
                        >
                            Read our story
                        </Link>
                    </div>
                </div>
            </section>

            {/* Favorites section */}
            <section aria-labelledby="favorites-heading">
                <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
                    <div className="sm:flex sm:items-baseline sm:justify-between">
                        <h2
                            id="favorites-heading"
                            className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl"
                        >
                            Top Reads
                        </h2>
                        <Link
                            to="/books"
                            className="hidden text-sm font-semibold text-indigo-600 hover:text-indigo-500 sm:block"
                        >
                            Browse all favorites
                            <span aria-hidden="true"> &rarr;</span>
                        </Link>
                    </div>

                    <div className="mt-6 grid grid-cols-1 gap-y-10 sm:grid-cols-3 sm:gap-x-6 sm:gap-y-0 lg:gap-x-8">
                        {favorites.map((favorite) => (
                            <div key={favorite.id} className="group relative">
                                <img
                                    alt={favorite.imageAlt}
                                    src={favorite.imageSrc}
                                    className="h-96 w-full rounded-lg object-cover group-hover:opacity-75 sm:aspect-[2/3] sm:h-auto border border-gray-200 shadow-sm"
                                />
                                <h3 className="mt-4 text-base font-semibold text-gray-900">
                                    <Link to={favorite.href}>
                                        <span className="absolute inset-0" />
                                        {favorite.name}
                                    </Link>
                                </h3>
                                <p className="mt-1 text-sm text-gray-500">
                                    {favorite.author}
                                </p>
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 sm:hidden">
                        <Link
                            to="/books"
                            className="block text-sm font-semibold text-indigo-600 hover:text-indigo-500"
                        >
                            Browse all favorites
                            <span aria-hidden="true"> &rarr;</span>
                        </Link>
                    </div>
                </div>
            </section>
        </>
    );
}
