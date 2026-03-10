import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import CircularProgress from '@mui/material/CircularProgress'
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import CloseIcon from '@mui/icons-material/Close'
import { usePhotoUpload } from '@/features/onboarding/hooks/usePhotoUpload'
import { useOnboardingStore } from '@/features/onboarding/stores/onboardingStore'

interface PhotoSlot {
  previewUrl: string | null
  key: string | null
  embedding: number[] | null
  status: 'empty' | 'uploading' | 'complete' | 'error'
  error: string | null
}

const INITIAL_SLOT: PhotoSlot = {
  previewUrl: null,
  key: null,
  embedding: null,
  status: 'empty',
  error: null,
}

export default function PhotoUploadStep() {
  const navigate = useNavigate()
  const setPhotos = useOnboardingStore((s) => s.setPhotos)

  const [slots, setSlots] = useState<[PhotoSlot, PhotoSlot]>([
    { ...INITIAL_SLOT },
    { ...INITIAL_SLOT },
  ])

  const upload1 = usePhotoUpload()
  const upload2 = usePhotoUpload()
  const uploads = useMemo(() => [upload1, upload2] as const, [upload1, upload2])

  const fileInput0Ref = useRef<HTMLInputElement>(null)
  const fileInput1Ref = useRef<HTMLInputElement>(null)
  const fileInputRefs = useMemo(() => [fileInput0Ref, fileInput1Ref], [])

  // Track preview URLs for cleanup on unmount
  const previewUrlsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    const urls = previewUrlsRef
    return () => {
      urls.current.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [])

  const handleFileSelect = useCallback(
    async (index: number, file: File) => {
      const previewUrl = URL.createObjectURL(file)
      previewUrlsRef.current.add(previewUrl)

      // Revoke previous preview URL if exists
      setSlots((prev) => {
        if (prev[index].previewUrl) {
          URL.revokeObjectURL(prev[index].previewUrl!)
          previewUrlsRef.current.delete(prev[index].previewUrl!)
        }
        const next: [PhotoSlot, PhotoSlot] = [...prev]
        next[index] = {
          previewUrl,
          key: null,
          embedding: null,
          status: 'uploading',
          error: null,
        }
        return next
      })

      // Upload via the hook
      const result = await uploads[index].uploadPhoto(file)

      if (result) {
        setSlots((prev) => {
          const next: [PhotoSlot, PhotoSlot] = [...prev]
          next[index] = {
            ...next[index],
            key: result.key,
            embedding: result.embedding,
            status: 'complete',
          }
          return next
        })
      } else {
        setSlots((prev) => {
          const next: [PhotoSlot, PhotoSlot] = [...prev]
          next[index] = {
            ...next[index],
            status: 'error',
            error: uploads[index].error ?? 'Upload failed',
          }
          return next
        })
      }
    },
    [uploads]
  )

  const handleRemove = useCallback((index: number) => {
    setSlots((prev) => {
      if (prev[index].previewUrl) {
        URL.revokeObjectURL(prev[index].previewUrl!)
        previewUrlsRef.current.delete(prev[index].previewUrl!)
      }
      const next: [PhotoSlot, PhotoSlot] = [...prev]
      next[index] = { ...INITIAL_SLOT }
      return next
    })
  }, [])

  const handleInputChange = useCallback(
    (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFileSelect(index, file)
      }
      // Reset input value so same file can be re-selected
      e.target.value = ''
    },
    [handleFileSelect]
  )

  const handleSlotClick = useCallback(
    (index: number) => {
      const slot = slots[index]
      if (slot.status === 'empty' || slot.status === 'error') {
        fileInputRefs[index].current?.click()
      }
    },
    [slots, fileInputRefs]
  )

  const handleContinue = useCallback(() => {
    const completedPhotos = slots.flatMap((slot) =>
      slot.status === 'complete' && slot.key && slot.embedding
        ? [{ key: slot.key, embedding: slot.embedding }]
        : []
    )

    setPhotos(completedPhotos)
    navigate('/onboarding/calibrate')
  }, [slots, setPhotos, navigate])

  // At least 1 photo must be successfully uploaded
  const completedCount = slots.filter((s) => s.status === 'complete').length
  const canContinue = completedCount >= 1

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        gap: 3,
      }}
    >
      {/* Header */}
      <Box sx={{ textAlign: 'center', pt: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
          Upload Your Outfits
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Share 1-2 photos of outfits you love
        </Typography>
      </Box>

      {/* Photo slots */}
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          justifyContent: 'center',
          flex: 1,
          alignItems: 'center',
        }}
      >
        {slots.map((slot, index) => {
          // Read progress directly from the upload hook (pure render read)
          const progress = slot.status === 'uploading' ? uploads[index].progress : 0

          return (
            <Box key={index} sx={{ width: '45%', maxWidth: 200 }}>
              {/* Hidden file input — NO capture attribute per iOS research */}
              <input
                ref={fileInputRefs[index]}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleInputChange(index, e)}
              />

              <Box
                onClick={() => handleSlotClick(index)}
                sx={{
                  position: 'relative',
                  aspectRatio: '3/4',
                  borderRadius: 2,
                  overflow: 'hidden',
                  cursor: slot.status === 'uploading' ? 'default' : 'pointer',
                  border: slot.status === 'empty' ? '2px dashed' : '2px solid',
                  borderColor:
                    slot.status === 'error'
                      ? 'error.main'
                      : slot.status === 'complete'
                        ? 'success.main'
                        : 'divider',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'background.paper',
                  transition: 'border-color 0.2s',
                  '&:hover': {
                    borderColor: slot.status === 'empty' ? 'primary.main' : undefined,
                  },
                }}
              >
                {/* Empty state */}
                {slot.status === 'empty' && (
                  <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
                    <AddAPhotoIcon sx={{ fontSize: 40, mb: 1, opacity: 0.6 }} />
                    <Typography variant="caption" display="block">
                      {index === 0 ? 'Outfit 1' : 'Outfit 2'}
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ opacity: 0.6 }}>
                      {index === 0 ? 'Required' : 'Optional'}
                    </Typography>
                  </Box>
                )}

                {/* Preview image (uploading, complete, or error) */}
                {slot.previewUrl && (
                  <Box
                    component="img"
                    src={slot.previewUrl}
                    alt={`Outfit ${index + 1}`}
                    sx={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      opacity: slot.status === 'uploading' ? 0.6 : 1,
                    }}
                  />
                )}

                {/* Uploading overlay */}
                {slot.status === 'uploading' && (
                  <Box
                    sx={{
                      position: 'absolute',
                      inset: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: 'rgba(0,0,0,0.3)',
                    }}
                  >
                    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                      <CircularProgress
                        variant="determinate"
                        value={progress}
                        size={56}
                        sx={{ color: 'white' }}
                      />
                      <Box
                        sx={{
                          position: 'absolute',
                          inset: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: 'white', fontWeight: 600 }}>
                          {progress}%
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Complete badge */}
                {slot.status === 'complete' && (
                  <CheckCircleIcon
                    sx={{
                      position: 'absolute',
                      bottom: 8,
                      right: 8,
                      color: 'success.main',
                      bgcolor: 'white',
                      borderRadius: '50%',
                      fontSize: 28,
                    }}
                  />
                )}

                {/* Error badge */}
                {slot.status === 'error' && (
                  <Box
                    sx={{
                      position: 'absolute',
                      inset: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: 'rgba(0,0,0,0.4)',
                    }}
                  >
                    <ErrorIcon sx={{ color: 'error.main', fontSize: 36, mb: 0.5 }} />
                    <Typography variant="caption" sx={{ color: 'white' }}>
                      Tap to retry
                    </Typography>
                  </Box>
                )}

                {/* Remove button */}
                {slot.status !== 'empty' && slot.status !== 'uploading' && (
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemove(index)
                    }}
                    sx={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                      bgcolor: 'rgba(0,0,0,0.5)',
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
                      width: 28,
                      height: 28,
                    }}
                  >
                    <CloseIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                )}
              </Box>

              {/* Slot label */}
              <Typography
                variant="caption"
                display="block"
                sx={{ textAlign: 'center', mt: 1, color: 'text.secondary' }}
              >
                {index === 0 ? 'Outfit 1' : 'Outfit 2'}
              </Typography>
            </Box>
          )
        })}
      </Box>

      {/* Continue button */}
      <Box sx={{ pb: 2 }}>
        <Button
          fullWidth
          variant="contained"
          size="large"
          disabled={!canContinue}
          onClick={handleContinue}
          sx={{ py: 1.5 }}
        >
          Continue
        </Button>
      </Box>
    </Box>
  )
}
