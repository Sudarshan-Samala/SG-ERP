import { Button } from './Button';
import { Modal } from './Modal';

export function ConfirmDialog({ isOpen, onClose, onConfirm, title, message }: any) {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title}>
            <p className="mb-4 text-gray-700">{message}</p>
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={onClose}>Cancel</Button>
                <Button variant="danger" onClick={onConfirm}>Delete</Button>
            </div>
        </Modal>
    );
}
