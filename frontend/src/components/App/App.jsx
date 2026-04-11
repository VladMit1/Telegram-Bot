import { useState } from 'react';
import { useGetContactsQuery } from '../../store/apiSlice';
import { motion, AnimatePresence } from 'framer-motion';
import {
   RefreshCw,
   Users,
   Calendar as CalendarIcon,
   Search,
} from 'lucide-react';

import { StudentCard } from '../Contacts/StudentCard';
import { StudentModal } from '../Contact/StudentModal';
//import { Calendar } from './components/Calendar/Calendar';

function App() {
   const [view, setView] = useState('list');
   const [searchQuery, setSearchQuery] = useState('');
   const [selectedStudent, setSelectedStudent] = useState(null);

   const {
      data: contacts = [],
      isLoading,
      isFetching,
      refetch,
   } = useGetContactsQuery();

   const filteredContacts = contacts.filter((c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase())
   );

   return (
      <div className="app-container">
         <header className="header">
            <div className="nav-tabs">
               <button
                  className={view === 'list' ? 'active' : ''}
                  onClick={() => setView('list')}
               >
                  <Users size={20} />
                  <span>Ученики</span>
               </button>
               <button
                  className={view === 'calendar' ? 'active' : ''}
                  onClick={() => setView('calendar')}
               >
                  <CalendarIcon size={20} />
                  <span>График</span>
               </button>
            </div>
            <button
               className={`refresh-btn ${isFetching ? 'spinning' : ''}`}
               onClick={refetch}
            >
               <RefreshCw size={20} />
            </button>
         </header>

         <main className="content">
            <AnimatePresence mode="wait">
               {view === 'list' ? (
                  <motion.div
                     key="list"
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                  >
                     <div className="search-wrapper">
                        <Search className="search-icon" size={18} />
                        <input
                           placeholder="Поиск ученика..."
                           value={searchQuery}
                           onChange={(e) => setSearchQuery(e.target.value)}
                        />
                     </div>
                     <div className="students-list">
                        {isLoading ? (
                           <p>Загрузка...</p>
                        ) : (
                           filteredContacts.map((s) => (
                              <StudentCard
                                 key={s.id}
                                 student={s}
                                 onOpen={setSelectedStudent}
                                 onSchedule={() => setView('calendar')}
                              />
                           ))
                        )}
                     </div>
                  </motion.div>
               ) : (
                  <div key="cal">Тут будет твой Календарь</div>
               )}
            </AnimatePresence>
         </main>

         <AnimatePresence>
            {selectedStudent && (
               <StudentModal
                  student={selectedStudent}
                  onClose={() => setSelectedStudent(null)}
               />
            )}
         </AnimatePresence>
      </div>
   );
}
export default App;
