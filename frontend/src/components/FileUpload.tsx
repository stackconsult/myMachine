'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
  extractedText?: string;
}

interface FileUploadProps {
  className?: string;
  onFileUploaded?: (file: UploadedFile) => void;
  maxFiles?: number;
  maxSize?: number;
  acceptedTypes?: string[];
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export function FileUpload({
  className,
  onFileUploaded,
  maxFiles = 5,
  maxSize = 10 * 1024 * 1024, // 10MB
  acceptedTypes = ['.pdf', '.docx', '.doc', '.txt', '.csv', '.json', '.xlsx', '.xls']
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const uploadFile = async (file: File): Promise<UploadedFile> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      
      return {
        id: result.file_id,
        name: file.name,
        size: file.size,
        status: 'success',
        extractedText: result.extracted_text
      };
    } catch (error: any) {
      return {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        status: 'error',
        error: error.message || 'Upload failed'
      };
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);

    // Add files with uploading status
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      status: 'uploading' as const
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Upload files
    const uploadPromises = acceptedFiles.map(async (file, index) => {
      const result = await uploadFile(file);
      
      setFiles(prev => prev.map(f => 
        f.id === newFiles[index].id ? result : f
      ));

      if (onFileUploaded && result.status === 'success') {
        onFileUploaded(result);
      }

      return result;
    });

    await Promise.all(uploadPromises);
    setIsUploading(false);
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    maxFiles,
    maxSize,
    accept: acceptedTypes.reduce((acc, type) => {
      if (type === '.pdf') acc['application/pdf'] = ['.pdf'];
      if (type === '.docx') acc['application/vnd.openxmlformats-officedocument.wordprocessingml.document'] = ['.docx'];
      if (type === '.doc') acc['application/msword'] = ['.doc'];
      if (type === '.txt') acc['text/plain'] = ['.txt'];
      if (type === '.csv') acc['text/csv'] = ['.csv'];
      if (type === '.json') acc['application/json'] = ['.json'];
      if (type === '.xlsx') acc['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = ['.xlsx'];
      if (type === '.xls') acc['application/vnd.ms-excel'] = ['.xls'];
      return acc;
    }, {} as Record<string, string[]>)
  });

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className={cn("file-upload", className)}>
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200",
          isDragActive && !isDragReject && "border-blue-500 bg-blue-50",
          isDragReject && "border-red-500 bg-red-50",
          !isDragActive && "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center gap-2">
          <Upload className={cn(
            "w-10 h-10",
            isDragActive && !isDragReject && "text-blue-500",
            isDragReject && "text-red-500",
            !isDragActive && "text-gray-400"
          )} />
          
          {isDragActive && !isDragReject ? (
            <p className="text-blue-600 font-medium">Drop files here...</p>
          ) : isDragReject ? (
            <p className="text-red-600 font-medium">File type not accepted</p>
          ) : (
            <>
              <p className="text-gray-600 font-medium">
                Drag & drop files here, or click to select
              </p>
              <p className="text-sm text-gray-400">
                Supported: {acceptedTypes.join(', ')} (max {formatFileSize(maxSize)})
              </p>
            </>
          )}
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map(file => (
            <div
              key={file.id}
              className={cn(
                "flex items-center justify-between p-3 rounded-lg border",
                file.status === 'error' && "border-red-200 bg-red-50",
                file.status === 'success' && "border-green-200 bg-green-50",
                file.status === 'uploading' && "border-blue-200 bg-blue-50"
              )}
            >
              <div className="flex items-center gap-3">
                <File className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-700">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  {file.error && (
                    <p className="text-xs text-red-600">{file.error}</p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {getStatusIcon(file.status)}
                {file.status !== 'uploading' && (
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-1 hover:bg-gray-200 rounded"
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Extracted text preview */}
      {files.some(f => f.extractedText) && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Extracted Text Preview</h4>
          {files.filter(f => f.extractedText).map(file => (
            <div key={file.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200 mb-2">
              <p className="text-xs font-medium text-gray-600 mb-1">{file.name}</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-5">
                {file.extractedText}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
