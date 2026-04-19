import { useState, useEffect } from 'react'
import { useGetContactsQuery } from '../../store/apiSlice'
import { motion, AnimatePresence } from 'framer-motion'
import {
   RefreshCw,
   Users,
   Calendar as CalendarIcon,
   Search,
} from 'lucide-react'
import { StudentCard } from '../Contacts/StudentCard'
import { StudentModal } from '../Contact/StudentModal'
import { Calendar } from '../Calendar/Calendar'

function App() {
   const [view, setView] = useState('list')
   const [searchQuery, setSearchQuery] = useState('')
   const [selectedStudent, setSelectedStudent] = useState(null)
   const [calendarContext, setCalendarContext] = useState(null)

   const {
      data: contacts = [],
      isLoading,
      isFetching,
      refetch,
   } = useGetContactsQuery()
   useEffect(() => {
      const params = new URLSearchParams(window.location.search)
      const studentIdFromUrl = params.get('studentId')

      if (studentIdFromUrl && contacts.length > 0) {
         const student = contacts.find(
            (c) => String(c.id) === String(studentIdFromUrl)
         )
         console.log(student, studentIdFromUrl, contacts)

         if (student) {
            // Оборачиваем в нулевой таймаут
            setTimeout(() => {
               setSelectedStudent(student)
            }, 0)
         }
      }
   }, [contacts])
   const navigateToCalendar = (student = null) => {
      setCalendarContext(student)
      setView('calendar')
   }

   return (
      <div className="app-container">
         <header className="header">
            <div className="nav-tabs">
               <button
                  className={view === 'list' ? 'active' : ''}
                  onClick={() => setView('list')}
               >
                  <Users size={20} /> <span>Ученики</span>
               </button>
               <button
                  className={view === 'calendar' ? 'active' : ''}
                  onClick={() => navigateToCalendar(null)}
               >
                  <CalendarIcon size={20} /> <span>График</span>
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
                     initial={{ opacity: 0, x: -10 }}
                     animate={{ opacity: 1, x: 0 }}
                     exit={{ opacity: 0, x: 10 }}
                  >
                     <div className="search-wrapper">
                        <Search className="search-icon" size={18} />
                        <input
                           placeholder="Поиск..."
                           value={searchQuery}
                           onChange={(e) => setSearchQuery(e.target.value)}
                        />
                     </div>
                     <div className="students-list">
                        {isLoading ? (
                           <p>Загрузка...</p>
                        ) : (
                           contacts
                              .filter((c) =>
                                 c.name
                                    .toLowerCase()
                                    .includes(searchQuery.toLowerCase())
                              )
                              .map((s) => (
                                 <StudentCard
                                    key={s.id}
                                    student={s}
                                    onOpen={() => setSelectedStudent(s)}
                                    onSchedule={() => navigateToCalendar(s)}
                                 />
                              ))
                        )}
                     </div>
                  </motion.div>
               ) : (
                  <motion.div
                     key="calendar"
                     initial={{ opacity: 0, x: 10 }}
                     animate={{ opacity: 1, x: 0 }}
                     exit={{ opacity: 0, x: -10 }}
                  >
                     <Calendar
                        initialStudent={calendarContext}
                        onContextClear={() => setCalendarContext(null)}
                     />
                  </motion.div>
               )}
            </AnimatePresence>
         </main>

         <AnimatePresence>
            {selectedStudent && (
               <StudentModal
                  student={selectedStudent}
                  onClose={() => setSelectedStudent(null)}
                  onSchedule={() => {
                     const s = selectedStudent
                     setSelectedStudent(null)
                     navigateToCalendar(s)
                  }}
               />
            )}
         </AnimatePresence>
      </div>
   )
}
export default App
