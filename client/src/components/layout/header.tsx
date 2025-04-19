import { useState } from 'react';
import { Bell } from 'lucide-react';
import { useLocation } from 'wouter';
import { useUser } from '@/context/user-context';

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  const { user } = useUser();
  const [, setLocation] = useLocation();
  const [showNotifications, setShowNotifications] = useState(false);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase();
  };

  const handleProfileClick = () => {
    setLocation('/profile');
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-md bg-primary flex items-center justify-center text-white font-bold mr-2">BB</div>
          <h1 className="text-xl font-bold text-primary">BimaBora</h1>
        </div>
        <div className="flex items-center">
          <button 
            className="p-2 mr-2 text-neutral-600 relative" 
            aria-label="Notifications"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell size={20} />
            <span className="absolute top-1 right-1 bg-primary w-2 h-2 rounded-full"></span>
          </button>
          <button 
            className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-primary font-bold"
            aria-label="Profile"
            onClick={handleProfileClick}
          >
            {user ? getInitials(user.fullName || 'User') : 'U'}
          </button>
        </div>
      </div>
    </header>
  );
}
