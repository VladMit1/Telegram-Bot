import { Trash2, Edit2, Clock, BookOpen } from 'lucide-react';
import { useDeleteLessonMutation } from '../../../store/apiSlice';

export const EventCard = ({ event, onEdit }) => {
   const [deleteLesson, { isLoading: isDeleting }] = useDeleteLessonMutation();

   const handleDelete = async () => {
      if (confirm(`Удалить урок ученика ${event.student}?`)) {
         await deleteLesson(event.id);
      }
   };

   return (
      <div className={`event-card ${isDeleting ? 'deleting' : ''}`}>
         <div className="event-time-block">
            <div className="time">{event.time}</div>
            <div className="duration">{event.duration} мин</div>
         </div>

         <div className="event-main-info">
            <h4>{event.student}</h4>
            <p>
               <BookOpen size={12} /> {event.topic || 'Без темы'}
            </p>
         </div>

         <div className="event-actions">
            <button className="action-btn edit" onClick={() => onEdit(event)}>
               <Edit2 size={18} />
            </button>
            <button
               className="action-btn delete"
               onClick={handleDelete}
               disabled={isDeleting}
            >
               <Trash2 size={18} />
            </button>
         </div>
      </div>
   );
};
