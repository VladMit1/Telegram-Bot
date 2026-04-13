import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import moment from 'moment';
import {
   ChevronLeft,
   ChevronRight,
   Plus,
   Calendar as CalendarIcon,
   List,
} from 'lucide-react';
import { WeekView } from './components/WeekView';
import { MonthView } from './components/MonthView';
import { EventCard } from './components/EventCard';

// Моковые данные с датами для проверки фильтрации
const MOCK_EVENTS = [
   {
      id: 1,
      time: '10:00',
      duration: '60 мин',
      student: 'Александр Г.',
      topic: 'Present Simple',
      date: '2026-04-13',
   },
   {
      id: 2,
      time: '14:30',
      duration: '45 мин',
      student: 'Мария Л.',
      topic: 'Reading Unit 4',
      date: '2026-04-14',
   },
   {
      id: 3,
      time: '09:00',
      duration: '60 мин',
      student: 'Иван П.',
      topic: 'Business English',
      date: '2026-04-13',
   },
];

export const Calendar = () => {
   const [selectedDate, setSelectedDate] = useState(moment());
   const [viewMode, setViewMode] = useState('week'); // 'week' | 'month'

   // Фильтрация событий: показываем только те, что совпадают с выбранным днем
   const dailyEvents = useMemo(() => {
      return MOCK_EVENTS.filter(
         (event) => event.date === selectedDate.format('YYYY-MM-DD')
      );
   }, [selectedDate]);

   const handlePrev = () => {
      setSelectedDate((prev) =>
         prev.clone().subtract(1, viewMode === 'week' ? 'week' : 'month')
      );
   };

   const handleNext = () => {
      setSelectedDate((prev) =>
         prev.clone().add(1, viewMode === 'week' ? 'week' : 'month')
      );
   };

   return (
      <div className="calendar-screen">
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
               <button onClick={handlePrev} className="icon-btn">
                  <ChevronLeft />
               </button>
               <div className="current-week-label">
                  {viewMode === 'week'
                     ? `Неделя ${selectedDate.format('w')}`
                     : 'Весь месяц'}
               </div>
               <button onClick={handleNext} className="icon-btn">
                  <ChevronRight />
               </button>
            </div>
         </header>

         <div className="calendar-body">
            <AnimatePresence mode="wait">
               {viewMode === 'week' ? (
                  <WeekView
                     key="week"
                     selectedDate={selectedDate}
                     onSelect={setSelectedDate}
                  />
               ) : (
                  <MonthView
                     key="month"
                     selectedDate={selectedDate}
                     onSelect={setSelectedDate}
                     events={MOCK_EVENTS} // Передаем ивенты, чтобы рисовать точки
                  />
               )}
            </AnimatePresence>
         </div>

         <section className="events-section">
            <div className="section-title">
               <h3>{selectedDate.format('D MMMM, dddd')}</h3>
               <button className="add-btn">
                  <Plus size={20} />
               </button>
            </div>

            <div className="event-list">
               {dailyEvents.length > 0 ? (
                  dailyEvents.map((event) => (
                     <EventCard key={event.id} event={event} />
                  ))
               ) : (
                  <div className="empty-state">
                     <p>На сегодня уроков нет</p>
                  </div>
               )}
            </div>
         </section>
      </div>
   );
};
