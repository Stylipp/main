import Box from '@mui/material/Box'
import IconButton, { type IconButtonProps } from '@mui/material/IconButton'
import UndoIcon from '@mui/icons-material/Undo'
import CloseIcon from '@mui/icons-material/Close'
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder'
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
        gap: { xs: 1.5, sm: 2.5 },
        py: { xs: 2, sm: 2.5 },
        pb: { xs: 3, sm: 3 },
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
          width: 44,
          height: 44,
          border: '2px solid',
          borderColor: canUndo && !disabled ? 'text.secondary' : 'action.disabledBackground',
          color: canUndo && !disabled ? 'text.secondary' : 'action.disabled',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.main',
            color: 'primary.main',
            bgcolor: 'rgba(91, 74, 228, 0.06)',
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
        whileTap={{ scale: 0.85 }}
        sx={{
          width: 60,
          height: 60,
          bgcolor: '#ffffff',
          color: 'error.main',
          border: '2.5px solid',
          borderColor: 'error.main',
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'error.main',
            color: '#ffffff',
          },
          '&.Mui-disabled': {
            bgcolor: 'transparent',
            borderColor: 'action.disabledBackground',
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
          borderColor: 'primary.main',
          color: 'primary.main',
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'primary.main',
            color: '#ffffff',
          },
          '&.Mui-disabled': {
            borderColor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <BookmarkBorderIcon sx={{ fontSize: 22 }} />
      </AnimatedIconButton>

      {/* Like button */}
      <AnimatedIconButton
        onClick={onLike}
        disabled={disabled}
        aria-label="Like"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.85 }}
        sx={{
          width: 60,
          height: 60,
          bgcolor: '#ffffff',
          color: 'success.main',
          border: '2.5px solid',
          borderColor: 'success.main',
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'success.main',
            color: '#ffffff',
          },
          '&.Mui-disabled': {
            bgcolor: 'transparent',
            borderColor: 'action.disabledBackground',
            color: 'action.disabled',
          },
        }}
      >
        <FavoriteIcon sx={{ fontSize: 28 }} />
      </AnimatedIconButton>
    </Box>
  )
}
