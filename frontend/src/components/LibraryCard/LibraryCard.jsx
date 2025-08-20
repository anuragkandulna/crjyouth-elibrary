import { useState } from "react";

export default function LibraryCard() {
    // Mock data - in real app, this would come from props or API
    const [libraryCard] = useState({
        libraryName: "CRJ Youth E-Library",
        customerName: "John Doe",
        email: "john.doe@example.com",
        userId: "LIB001234",
        registrationDate: "2024-01-15",
        registeredOffice: "Main Library Building, Downtown",
    });

    const [transactions] = useState([
        {
            id: 1,
            bookName: "The Great Gatsby",
            author: "F. Scott Fitzgerald",
            bookCopyId: "BC001",
            issueDate: "2024-01-20",
            dueDate: "2024-02-20",
            returnDate: "2024-02-18",
            librarian: "Sarah Johnson",
            fine: "$0.00",
            remarks: "Returned on time",
        },
        {
            id: 2,
            bookName: "To Kill a Mockingbird",
            author: "Harper Lee",
            bookCopyId: "BC002",
            issueDate: "2024-02-01",
            dueDate: "2024-03-01",
            returnDate: "2024-03-05",
            librarian: "Mike Wilson",
            fine: "$2.00",
            remarks: "Returned late - 4 days overdue",
        },
        {
            id: 3,
            bookName: "1984",
            author: "George Orwell",
            bookCopyId: "BC003",
            issueDate: "2024-03-10",
            dueDate: "2024-04-10",
            returnDate: null,
            librarian: "Emily Davis",
            fine: "$0.00",
            remarks: "Currently borrowed",
        },
    ]);

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Main Content */}
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-lg shadow-sm border p-8">
                    <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
                        Library Card
                    </h2>

                    {/* User Information Section */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div className="border-l-4 border-blue-500 pl-6">
                            <h3 className="text-xl font-semibold text-gray-900 mb-4">
                                Library Information
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <span className="font-medium text-gray-700">
                                        Library Name:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.libraryName}
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">
                                        Registered Office:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.registeredOffice}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="border-l-4 border-green-500 pl-6">
                            <h3 className="text-xl font-semibold text-gray-900 mb-4">
                                Customer Information
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <span className="font-medium text-gray-700">
                                        Customer Name:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.customerName}
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">
                                        Email:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.email}
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">
                                        User ID:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.userId}
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">
                                        Registration Date:
                                    </span>
                                    <span className="ml-2 text-gray-900">
                                        {libraryCard.registrationDate}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Transaction History Section */}
                    <div className="border-l-4 border-purple-500 pl-6 mb-6">
                        <h3 className="text-xl font-semibold text-gray-900 mb-4">
                            Transaction History
                        </h3>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                        <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Sl No.
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Book Name + Author
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Book Copy ID
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Issue Date
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Due Date
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Return Date
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Librarian
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Fine
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                                        Remarks
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {transactions.map((transaction) => (
                                    <tr
                                        key={transaction.id}
                                        className="hover:bg-gray-50"
                                    >
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.id}
                                        </td>
                                        <td className="px-4 py-3 text-sm border-b">
                                            <div>
                                                <div className="font-medium text-gray-900">
                                                    {transaction.bookName}
                                                </div>
                                                <div className="text-gray-500">
                                                    {transaction.author}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.bookCopyId}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.issueDate}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.dueDate}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.returnDate || "-"}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.librarian}
                                        </td>
                                        <td className="px-4 py-3 text-sm border-b">
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                    transaction.fine === "$0.00"
                                                        ? "bg-green-100 text-green-800"
                                                        : "bg-red-100 text-red-800"
                                                }`}
                                            >
                                                {transaction.fine}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900 border-b">
                                            {transaction.remarks}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Summary Section */}
                    <div className="mt-8 pt-6 border-t border-gray-200">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                    {transactions.length}
                                </div>
                                <div className="text-sm text-gray-600">
                                    Total Transactions
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">
                                    {
                                        transactions.filter((t) => t.returnDate)
                                            .length
                                    }
                                </div>
                                <div className="text-sm text-gray-600">
                                    Books Returned
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-red-600">
                                    {
                                        transactions.filter(
                                            (t) => !t.returnDate
                                        ).length
                                    }
                                </div>
                                <div className="text-sm text-gray-600">
                                    Books Borrowed
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-12 pt-8 border-t border-gray-200 text-center">
                        <p className="text-gray-500 text-sm">
                            This library card is valid for the current academic
                            year and must be renewed annually.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
