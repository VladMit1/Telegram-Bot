import { motion } from 'framer-motion';
import moment from 'moment';

export const WeekView = ({ selectedDate, onSelect }) => {
   const startOfWeek = selectedDate.clone().startOf('isoWeek');
   const days = Array.from({ length: 7 }, (_, i) =>
      startOfWeek.clone().add(i, 'days')
   );

   return (
      <motion.div
         className="week-strip"
         initial={{ opacity: 0, x: -10 }}
         animate={{ opacity: 1, x: 0 }}
         exit={{ opacity: 0, x: 10 }}
      >
         {days.map((day) => {
            const isToday = day.isSame(moment(), 'day'); // Сравнивает день, месяц и год с реальным "сегодня"
            const isSelected = day.isSame(selectedDate, 'day'); // Сравнивает с выбранной датой
            return (
               <div
                  key={day.format('YYYY-MM-DD')} // Используем полную дату как ключ
                  className={`day-card ${isSelected ? 'active' : ''} ${isToday ? 'today' : ''}`}
                  onClick={() => onSelect(day)}
               >
                  <span className="label">{day.format('dd')}</span>
                  <span className="num">{day.date()}</span>
               </div>
            );
         })}
      </motion.div>
   );
};
