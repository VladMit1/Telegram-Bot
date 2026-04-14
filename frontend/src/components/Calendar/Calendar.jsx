import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import moment from 'moment';
import { ChevronLeft, ChevronRight, Plus, X } from 'lucide-react';
import { WeekView } from './components/WeekView';
import { MonthView } from './components/MonthView';
import { EventCard } from './components/EventCard';
import { AddEventModal } from './components/AddEventModal';
import './Calendar.scss';
import { useGetLessonsQuery } from '../../store/apiSlice';

export const Calendar = ({ initialStudent, onContextClear }) => {
   const [selectedDate, setSelectedDate] = useState(moment());
   const [viewMode, setViewMode] = useState('week');
   const [modalAddOpen, setModalAddOpen] = useState(false);
   const [pendingStudent, setPendingStudent] = useState(initialStudent);

   const { data: allLessons = [], isLoading } = useGetLessonsQuery();
   const dailyEvents = useMemo(() => {
      const dateStr = selectedDate.format('YYYY-MM-DD');
      return allLessons
         .filter((lesson) => lesson.lesson_date === dateStr)
         .sort((a, b) => a.lesson_time.localeCompare(b.lesson_time)); // Сортировка по времени
   }, [allLessons, selectedDate]);
   const handleDateSelect = (date) => {
      setSelectedDate(date);
      if (pendingStudent) {
         setModalAddOpen(true);
      }
   };

   const handleCloseModal = () => {
      setModalAddOpen(false);
      setPendingStudent(null);
      onContextClear();
   };

   return (
      <div className="calendar-screen">
         <AnimatePresence>
            {pendingStudent && !modalAddOpen && (
               <motion.div
                  initial={{ y: -50 }}
                  animate={{ y: 0 }}
                  exit={{ y: -50 }}
                  className="selection-hint"
               >
                  <span>
                     Выберите дату для <b>{pendingStudent.name}</b>
                  </span>
                  <button
                     onClick={() => {
                        setPendingStudent(null);
                        onContextClear();
                     }}
                  >
                     <X size={14} />
                  </button>
               </motion.div>
            )}
         </AnimatePresence>

         <header className="calendar-header">
            <div className="nav-row">
               <div className="date-info">
                  <h2>{selectedDate.format('MMMM')}</h2>
                  <span>{selectedDate.format('YYYY')}</span>
               </div>
               <div className="view-switcher">
                  <button
                     className={viewMode === 'week' ? 'active' : ''}
                     onClick={() => setViewMode('week')}
                  >
                     Неделя
                  </button>
                  <button
                     className={viewMode === 'month' ? 'active' : ''}
                     onClick={() => setViewMode('month')}
                  >
                     Месяц
                  </button>
               </div>
            </div>
            <div className="controls-row">
               <button
                  onClick={() =>
                     setSelectedDate((prev) =>
                        prev
                           .clone()
                           .subtract(1, viewMode === 'week' ? 'week' : 'month')
                     )
                  }
                  className="icon-btn"
               >
                  <ChevronLeft />
               </button>
               <div className="current-week-label">
                  {viewMode === 'week'
                     ? `Неделя ${selectedDate.format('w')}`
                     : 'Весь месяц'}
               </div>
               <button
                  onClick={() =>
                     setSelectedDate((prev) =>
                        prev
                           .clone()
                           .add(1, viewMode === 'week' ? 'week' : 'month')
                     )
                  }
                  className="icon-btn"
               >
                  <ChevronRight />
               </button>
            </div>
         </header>

         <div className="calendar-body">
            {viewMode === 'week' ? (
               <WeekView
                  selectedDate={selectedDate}
                  onSelect={handleDateSelect}
               />
            ) : (
               <MonthView
                  selectedDate={selectedDate}
                  onSelect={handleDateSelect}
                  events={[]}
               />
            )}
         </div>

         <section className="events-section">
            <div className="section-title">
               <h3>{selectedDate.format('D MMMM, dddd')}</h3>

               {/* Прячем плюс, если мы в режиме выбора даты для конкретного ученика */}
               {!pendingStudent && (
                  <motion.button
                     initial={{ scale: 0, opacity: 0 }}
                     animate={{ scale: 1, opacity: 1 }}
                     exit={{ scale: 0, opacity: 0 }}
                     className="add-btn"
                     onClick={() => setModalAddOpen(true)}
                  >
                     <Plus size={20} />
                  </motion.button>
               )}
            </div>

            <div className="event-list">
               {dailyEvents.length > 0 ? (
                  dailyEvents.map((event) => (
                     <EventCard
                        key={event.id}
                        event={{
                           ...event,
                           // Приводим ключи API к тем, что ожидает EventCard
                           time: event.lesson_time,
                           student: event.student_name || 'Ученик', // Предполагая, что бэк вернет имя
                           duration: `${event.duration} мин`,
                        }}
                     />
                  ))
               ) : (
                  <div className="empty-state">
                     <p>На сегодня уроков нет</p>
                  </div>
               )}
            </div>
         </section>

         {modalAddOpen && (
            <AddEventModal
               onClose={handleCloseModal}
               selectedDate={selectedDate}
               initialStudent={pendingStudent}
            />
         )}
      </div>
   );
};
