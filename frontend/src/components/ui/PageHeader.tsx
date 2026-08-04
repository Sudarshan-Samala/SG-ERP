export function PageHeader({ title, description, action }: { title: string, description?: string, action?: React.ReactNode }) {
    return (
        <div className="flex justify-between items-center mb-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
                {description && <p className="text-gray-500">{description}</p>}
            </div>
            {action}
        </div>
    );
}
