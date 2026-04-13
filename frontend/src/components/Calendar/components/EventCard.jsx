import { ChevronRight } from 'lucide-react';

export const EventCard = ({ event }) => {
   return (
      <div className="event-card">
         <div className="status-indicator" />

         <div className="event-time-block">
            <div className="time">{event.time}</div>
            <div className="duration">{event.duration}</div>
         </div>

         <div className="event-main-info">
            <div className="student-name">
               <h4>{event.student}</h4>
            </div>
            <p className="topic">{event.topic}</p>
         </div>

         <button className="details-button">
            <ChevronRight size={20} />
         </button>
      </div>
   );
};
