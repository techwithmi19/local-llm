import "./FileAttachment.css";

interface FileAttachmentProps {
  filename: string;
  status?: string;
  onRemove?: () => void;
  disabled?: boolean;
}

function FileAttachment({
  filename,
  status,
  onRemove,
  disabled = false,
}: FileAttachmentProps) {
  return (
    <div className="file-attachment">
      <span className="file-attachment-icon">📄</span>

      <span className="file-attachment-name">{filename}</span>

      {status && (
        <span className={`file-attachment-status ${status}`}>
          {status}
        </span>
      )}

      {onRemove && (
        <button
          type="button"
          className="file-attachment-remove"
          onClick={onRemove}
          disabled={disabled}
          aria-label={`Remove ${filename}`}
        >
          ×
        </button>
      )}
    </div>
  );
}

export default FileAttachment;
