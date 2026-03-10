import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface OnboardingState {
  currentStep: number
  photoKeys: string[]
  photoEmbeddings: number[][]
  calibrationItems: string[]
  calibrationLikes: string[]
  calibrationDislikes: string[]
  isComplete: boolean

  addPhoto: (key: string, embedding: number[]) => void
  setPhotos: (photos: Array<{ key: string; embedding: number[] }>) => void
  removePhoto: (index: number) => void
  setCalibrationItems: (ids: string[]) => void
  addLike: (productId: string) => void
  addDislike: (productId: string) => void
  complete: () => void
  reset: () => void
}

const initialState = {
  currentStep: 0,
  photoKeys: [] as string[],
  photoEmbeddings: [] as number[][],
  calibrationItems: [] as string[],
  calibrationLikes: [] as string[],
  calibrationDislikes: [] as string[],
  isComplete: false,
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      ...initialState,

      addPhoto: (key: string, embedding: number[]) =>
        set((state) => ({
          photoKeys: [...state.photoKeys, key],
          photoEmbeddings: [...state.photoEmbeddings, embedding],
        })),

      setPhotos: (photos) =>
        set({
          photoKeys: photos.map((photo) => photo.key),
          photoEmbeddings: photos.map((photo) => photo.embedding),
          calibrationItems: [],
          calibrationLikes: [],
          calibrationDislikes: [],
          isComplete: false,
        }),

      removePhoto: (index: number) =>
        set((state) => ({
          photoKeys: state.photoKeys.filter((_, i) => i !== index),
          photoEmbeddings: state.photoEmbeddings.filter((_, i) => i !== index),
        })),

      setCalibrationItems: (ids: string[]) => set({ calibrationItems: ids }),

      addLike: (productId: string) =>
        set((state) => ({
          calibrationLikes: [...state.calibrationLikes, productId],
        })),

      addDislike: (productId: string) =>
        set((state) => ({
          calibrationDislikes: [...state.calibrationDislikes, productId],
        })),

      complete: () => set({ isComplete: true }),

      reset: () => set(initialState),
    }),
    {
      name: 'stylipp-onboarding',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentStep: state.currentStep,
        photoKeys: state.photoKeys,
        photoEmbeddings: state.photoEmbeddings,
        calibrationLikes: state.calibrationLikes,
        calibrationDislikes: state.calibrationDislikes,
      }),
    }
  )
)
