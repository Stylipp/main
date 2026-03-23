import Box from '@mui/material/Box'
import IconButton, { type IconButtonProps } from '@mui/material/IconButton'
import UndoIcon from '@mui/icons-material/Undo'
import CloseIcon from '@mui/icons-material/Close'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import FavoriteIcon from '@mui/icons-material/Favorite'
import { motion, type MotionProps } from 'framer-motion'

type AnimatedIconButtonProps = IconButtonProps & MotionProps
const AnimatedIconButton = motion.create(IconButton) as React.FC<AnimatedIconButtonProps>

interface SwipeActionsProps {
  onLike: () => void
  onDislike: () => void
  onSave: () => void
  onUndo: () => void
  canUndo: boolean
  disabled: boolean
}

export function SwipeActions({
  onLike,
  onDislike,
  onSave,
  onUndo,
  canUndo,
  disabled,
}: SwipeActionsProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 2,
        py: 2,
      }}
    >
      {/* Undo button */}
      <AnimatedIconButton
        onClick={onUndo}
        disabled={!canUndo || disabled}
        aria-label="Undo"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        sx={{
          width: 40,
          height: 40,
          border: '2px solid',
          borderColor: 'action.disabled',
          color: 'text.secondary',
          '&:hover': {
            borderColor: 'text.secondary',
          },
          '&.Mui-disabled': {
            borderColor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <UndoIcon sx={{ fontSize: 20 }} />
      </AnimatedIconButton>

      {/* Dislike button */}
      <AnimatedIconButton
        onClick={onDislike}
        disabled={disabled}
        aria-label="Dislike"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        sx={{
          width: 56,
          height: 56,
          bgcolor: 'error.main',
          color: '#ffffff',
          '&:hover': {
            bgcolor: 'error.dark',
          },
          '&.Mui-disabled': {
            bgcolor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <CloseIcon sx={{ fontSize: 28 }} />
      </AnimatedIconButton>

      {/* Save button */}
      <AnimatedIconButton
        onClick={onSave}
        disabled={disabled}
        aria-label="Save"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        sx={{
          width: 48,
          height: 48,
          border: '2px solid',
          borderColor: 'secondary.main',
          color: 'secondary.main',
          '&:hover': {
            bgcolor: 'rgba(236, 72, 153, 0.08)',
          },
          '&.Mui-disabled': {
            borderColor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <BookmarkIcon sx={{ fontSize: 24 }} />
      </AnimatedIconButton>

      {/* Like button */}
      <AnimatedIconButton
        onClick={onLike}
        disabled={disabled}
        aria-label="Like"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        sx={{
          width: 56,
          height: 56,
          bgcolor: 'success.main',
          color: '#ffffff',
          '&:hover': {
            bgcolor: 'success.dark',
          },
          '&.Mui-disabled': {
            bgcolor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <FavoriteIcon sx={{ fontSize: 28 }} />
      </AnimatedIconButton>
    </Box>
  )
}
