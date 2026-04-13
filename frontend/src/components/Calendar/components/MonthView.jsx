import { motion } from 'framer-motion';
import moment from 'moment';
export const MonthView = ({ selectedDate, onSelect, events }) => {
   const startOfMonth = selectedDate.clone().startOf('month');
   const startGrid = startOfMonth.clone().startOf('isoWeek');

   // Генерируем ровно 42 дня (6 недель)
   const cells = Array.from({ length: 42 }, (_, i) =>
      startGrid.clone().add(i, 'days')
   );

   return (
      <motion.div
         className="month-grid-view"
         initial={{ opacity: 0, scale: 0.95 }}
         animate={{ opacity: 1, scale: 1 }}
      >
         <div className="grid-header">
            {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
               <span key={d}>{d}</span>
            ))}
         </div>
         <div className="grid-cells">
            {cells.map((day) => {
               const isSelected = day.isSame(selectedDate, 'day');
               const isCurrentMonth = day.isSame(selectedDate, 'month');
               const hasEvents = events.some(
                  (e) => e.date === day.format('YYYY-MM-DD')
               );
               const isToday = day.isSame(moment(), 'day');
               return (
                  <div
                     key={day.format('YYYY-MM-DD')}
                     className={`grid-cell 
                  ${isSelected ? 'active' : ''} 
                  ${isToday ? 'today' : ''} 
                  ${!isCurrentMonth ? 'outside' : ''}`}
                     onClick={() => onSelect(day)}
                  >
                     <span>{day.date()}</span>
                     {hasEvents && <div className="dot" />}
                  </div>
               );
            })}
         </div>
      </motion.div>
   );
};
