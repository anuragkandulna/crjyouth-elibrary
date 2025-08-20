import {
    LIBRARY_NAME,
    LIBRARY_EMAIL,
    LIBRARY_ADDRESS,
} from "../../constants/constants";

export default function Credits() {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-lg shadow-sm border p-8">
                    <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
                        Credits & Attributions
                    </h2>

                    <div className="space-y-8">
                        {/* Freepik Image Credit */}
                        <div className="border-l-4 border-indigo-500 pl-6">
                            <h3 className="text-xl font-semibold text-gray-900 mb-3">
                                Library Student Image
                            </h3>
                            <p className="text-gray-600 mb-4">
                                The library student learning image used in this
                                application is provided by Freepik.
                            </p>
                            <div className="bg-gray-50 rounded-lg p-4">
                                <p className="text-sm text-gray-700 mb-2">
                                    <strong>Source:</strong>{" "}
                                    <a
                                        href="https://www.freepik.com/free-photo/young-student-learning-library_21138916.htm#fromView=search&page=1&position=10&uuid=e80da14a-c03a-4a72-b70f-ea145af7c71b&query=library"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-indigo-600 hover:text-indigo-500 underline"
                                    >
                                        Young Student Learning in Library
                                    </a>
                                </p>
                                <p className="text-sm text-gray-700">
                                    <strong>Attribution:</strong> Image by{" "}
                                    <a
                                        href="https://www.freepik.com"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-indigo-600 hover:text-indigo-500 underline"
                                    >
                                        Freepik
                                    </a>
                                </p>
                            </div>
                        </div>

                        {/* Open Library API Credit */}
                        <div className="border-l-4 border-green-500 pl-6">
                            <h3 className="text-xl font-semibold text-gray-900 mb-3">
                                Book Cover Images
                            </h3>
                            <p className="text-gray-600 mb-4">
                                Book cover images are provided through the Open
                                Library Covers API, which offers access to a
                                vast collection of book covers and author
                                photos.
                            </p>
                            <div className="bg-gray-50 rounded-lg p-4">
                                <p className="text-sm text-gray-700 mb-2">
                                    <strong>API Documentation:</strong>{" "}
                                    <a
                                        href="https://openlibrary.org/dev/docs/api/covers"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-indigo-600 hover:text-indigo-500 underline"
                                    >
                                        Open Library Covers API
                                    </a>
                                </p>
                                <p className="text-sm text-gray-700 mb-2">
                                    <strong>Service Provider:</strong>{" "}
                                    <a
                                        href="https://openlibrary.org"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-indigo-600 hover:text-indigo-500 underline"
                                    >
                                        Open Library
                                    </a>
                                </p>
                                <p className="text-sm text-gray-700">
                                    <strong>Note:</strong> Open Library is an
                                    initiative of the Internet Archive, a
                                    501(c)(3) non-profit organization building a
                                    digital library of Internet sites and other
                                    cultural artifacts.
                                </p>
                            </div>
                        </div>

                        {/* Additional Information */}
                        <div className="border-l-4 border-yellow-500 pl-6">
                            <h3 className="text-xl font-semibold text-gray-900 mb-3">
                                Usage Guidelines
                            </h3>
                            <div className="bg-yellow-50 rounded-lg p-4">
                                <ul className="text-sm text-gray-700 space-y-2">
                                    <li>
                                        • Freepik images are used under their
                                        free license terms
                                    </li>
                                    <li>
                                        • Open Library covers are used following
                                        their API guidelines
                                    </li>
                                    <li>
                                        • Proper attribution is provided as
                                        required by both services
                                    </li>
                                    <li>
                                        • Images are used for educational and
                                        library management purposes only
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-12 pt-8 border-t border-gray-200 text-center">
                        <p className="text-gray-500 text-sm">
                            This application respects intellectual property
                            rights and provides proper attribution to all
                            external resources used.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
