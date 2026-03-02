import { useState, useCallback } from 'react'
import imageCompression from 'browser-image-compression'
import api from '@/shared/hooks/useApi'

interface UploadResult {
  key: string
  url: string
  embedding: number[]
}

interface UsePhotoUploadReturn {
  uploadPhoto: (file: File) => Promise<UploadResult | null>
  isUploading: boolean
  progress: number
  error: string | null
}

const COMPRESSION_OPTIONS = {
  maxSizeMB: 1,
  maxWidthOrHeight: 1920,
  useWebWorker: true,
}

export function usePhotoUpload(): UsePhotoUploadReturn {
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const uploadPhoto = useCallback(async (file: File): Promise<UploadResult | null> => {
    setIsUploading(true)
    setProgress(0)
    setError(null)

    try {
      // Compress client-side (0-50% progress)
      const compressed = await imageCompression(file, {
        ...COMPRESSION_OPTIONS,
        onProgress: (pct: number) => setProgress(Math.round(pct * 0.5)),
      })

      // Upload to backend (50-100% progress)
      const formData = new FormData()
      formData.append('file', compressed, file.name)

      const response = await api.post<UploadResult>('/onboarding/photos', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            setProgress(50 + Math.round((e.loaded / e.total) * 50))
          }
        },
      })

      setProgress(100)
      return response.data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to upload photo'
      setError(message)
      return null
    } finally {
      setIsUploading(false)
    }
  }, [])

  return { uploadPhoto, isUploading, progress, error }
}
