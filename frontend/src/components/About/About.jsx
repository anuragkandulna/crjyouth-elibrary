import group_discussion from "../../assets/group_discussion.jpg";

const values = [
    {
        name: "Be world-class",
        icon: "🌟",
        description:
            "We aim to provide a library experience that sets the standard — from curated collections to innovative digital tools — inspiring readers to dream bigger and reach further.",
    },
    {
        name: "Share everything you know",
        icon: "🤝",
        description:
            "Knowledge grows when it's shared. We encourage open exchange of ideas, resources, and insights so everyone in our community benefits and learns together.",
    },
    {
        name: "Always learning",
        icon: "📚",
        description:
            "A library is never finished. We constantly explore new books, technologies, and ideas to keep our shelves and services fresh, relevant, and engaging.",
    },
    {
        name: "Be supportive",
        icon: "💪",
        description:
            "We believe in lifting each other up. Whether it's guiding someone to their next favorite book or supporting learning journeys, we're here to help.",
    },
    {
        name: "Take responsibility",
        icon: "🛡️",
        description:
            "We honor the trust placed in us to safeguard knowledge, maintain resources, and serve our members with integrity and accountability.",
    },
    {
        name: "Enjoy downtime",
        icon: "😌",
        description:
            "A library is also a place of calm. We embrace the joy of quiet reading, reflection, and the simple pleasure of losing yourself in a good book.",
    },
];
const team = [
    {
        name: "Michael Foster",
        role: "Library Director",
        imageUrl:
            "https://images.unsplash.com/photo-1519244703995-f4e0f30006d5?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
    {
        name: "Dries Vincent",
        role: "Youth Services Librarian",
        imageUrl:
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
    {
        name: "Lindsay Walton",
        role: "Reference Librarian",
        imageUrl:
            "https://images.unsplash.com/photo-1517841905240-472988babdf9?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
    {
        name: "Courtney Henry",
        role: "Children's Librarian",
        imageUrl:
            "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
    {
        name: "Tom Cook",
        role: "Technical Services Manager",
        imageUrl:
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
    {
        name: "Whitney Francis",
        role: "Library Assistant",
        imageUrl:
            "https://images.unsplash.com/photo-1517365830460-955ce3ccd263?ixlib=rb-=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=8&w=1024&h=1024&q=80",
    },
];

export default function About() {
    return (
        <>
            {/* Hero section */}

            {/* Image section with floating content */}
            <div className="relative">
                <img
                    alt=""
                    src={group_discussion}
                    className="w-screen h-auto object-cover outline outline-1 -outline-offset-1 outline-black/5"
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                    <div className="text-center text-white px-6 max-w-4xl">
                        <h1 className="text-pretty text-5xl font-semibold tracking-tight sm:text-7xl">
                            Empowering youth through knowledge and discovery
                        </h1>
                        <p className="mt-8 text-pretty text-lg font-medium sm:max-w-md sm:text-xl/8 lg:max-w-none">
                            Welcome to Youth Library, where every book opens a
                            door to new possibilities. We're dedicated to
                            fostering a love of reading, supporting educational
                            growth, and creating a vibrant community space where
                            young minds can explore, learn, and connect with the
                            world around them.
                        </p>
                    </div>
                </div>
            </div>

            {/* Feature section */}
            <div className="mx-auto mt-16 max-w-7xl px-6 lg:px-8">
                <div className="mx-auto max-w-2xl lg:mx-0">
                    <h2 className="text-pretty text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
                        Our values
                    </h2>
                    <p className="mt-6 text-lg/8 text-gray-700">
                        We are committed to upholding these values in everything
                        we do, ensuring that our library remains a vibrant,
                        inclusive, and inspiring space for all.
                    </p>
                </div>
                <dl className="mx-auto mt-8 grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 text-base/7 sm:grid-cols-2 lg:mx-0 lg:max-w-none lg:grid-cols-3">
                    {values.map((value) => (
                        <div key={value.name} className="text-center">
                            <div className="flex justify-center mb-4">
                                <span className="text-4xl">{value.icon}</span>
                            </div>
                            <dt className="font-semibold text-gray-900 text-lg mb-3">
                                {value.name}
                            </dt>
                            <dd className="text-gray-600 leading-relaxed">
                                {value.description}
                            </dd>
                        </div>
                    ))}
                </dl>
            </div>

            {/* Logo cloud */}
            <div className="relative isolate -z-10 mt-32 sm:mt-48">
                <div className="absolute inset-x-0 top-1/2 -z-10 flex -translate-y-1/2 justify-center overflow-hidden [mask-image:radial-gradient(50%_45%_at_50%_55%,white,transparent)]">
                    <svg
                        aria-hidden="true"
                        className="h-[40rem] w-[80rem] flex-none stroke-gray-200"
                    >
                        <defs>
                            <pattern
                                x="50%"
                                y="50%"
                                id="e9033f3e-f665-41a6-84ef-756f6778e6fe"
                                width={200}
                                height={200}
                                patternUnits="userSpaceOnUse"
                                patternTransform="translate(-100 0)"
                            >
                                <path d="M.5 200V.5H200" fill="none" />
                            </pattern>
                        </defs>
                        <svg
                            x="50%"
                            y="50%"
                            className="overflow-visible fill-gray-50"
                        >
                            <path
                                d="M-300 0h201v201h-201Z M300 200h201v201h-201Z"
                                strokeWidth={0}
                            />
                        </svg>
                        <rect
                            fill="url(#e9033f3e-f665-41a6-84ef-756f6778e6fe)"
                            width="100%"
                            height="100%"
                            strokeWidth={0}
                        />
                    </svg>
                </div>
                <div className="mx-auto max-w-7xl px-6 lg:px-8">
                    <h2 className="text-center text-lg/8 font-semibold text-gray-900">
                        Trusted by educators and families
                    </h2>
                    <div className="mx-auto mt-10 grid max-w-lg grid-cols-4 items-center gap-x-8 gap-y-10 sm:max-w-xl sm:grid-cols-6 sm:gap-x-10 lg:mx-0 lg:max-w-none lg:grid-cols-5">
                        <img
                            alt="Transistor"
                            src="https://tailwindcss.com/plus-assets/img/logos/158x48/transistor-logo-gray-900.svg"
                            width={158}
                            height={48}
                            className="col-span-2 max-h-12 w-full object-contain lg:col-span-1"
                        />
                        <img
                            alt="Reform"
                            src="https://tailwindcss.com/plus-assets/img/logos/158x48/reform-logo-gray-900.svg"
                            width={158}
                            height={48}
                            className="col-span-2 max-h-12 w-full object-contain lg:col-span-1"
                        />
                        <img
                            alt="Tuple"
                            src="https://tailwindcss.com/plus-assets/img/logos/158x48/tuple-logo-gray-900.svg"
                            width={158}
                            height={48}
                            className="col-span-2 max-h-12 w-full object-contain lg:col-span-1"
                        />
                        <img
                            alt="SavvyCal"
                            src="https://tailwindcss.com/plus-assets/img/logos/158x48/savvycal-logo-gray-900.svg"
                            width={158}
                            height={48}
                            className="col-span-2 max-h-12 w-full object-contain sm:col-start-2 lg:col-span-1"
                        />
                        <img
                            alt="Statamic"
                            src="https://tailwindcss.com/plus-assets/img/logos/158x48/statamic-logo-gray-900.svg"
                            width={158}
                            height={48}
                            className="col-span-2 col-start-2 max-h-12 w-full object-contain sm:col-start-auto lg:col-span-1"
                        />
                    </div>
                </div>
            </div>

            {/* Team section */}
            <div className="mx-auto mt-2 max-w-7xl px-6 lg:px-8">
                <div className="mx-auto max-w-2xl lg:mx-0">
                    <h2 className="text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
                        Our team
                    </h2>
                    <p className="mt-4 text-lg text-gray-600">
                        We're a dedicated team of readers, learners, and
                        innovators committed to making knowledge accessible and
                        engaging. Together, we strive to build a vibrant library
                        experience that inspires curiosity, fosters growth, and
                        connects communities.
                    </p>
                </div>
                <ul
                    role="list"
                    className="mt-6 grid grid-cols-2 gap-x-8 gap-y-16 text-center sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
                >
                    {team.map((person) => (
                        <li key={person.name}>
                            <img
                                alt=""
                                src={person.imageUrl}
                                className="mx-auto size-24 rounded-full outline outline-1 -outline-offset-1 outline-black/5"
                            />
                            <h3 className="mt-6 text-base/7 font-semibold tracking-tight text-gray-900">
                                {person.name}
                            </h3>
                            <p className="text-sm/6 text-gray-600">
                                {person.role}
                            </p>
                        </li>
                    ))}
                </ul>
            </div>
        </>
    );
}
