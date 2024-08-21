import React from 'react';

const Header = () => {
    return <div className="h-full flex flex-col flex-1 mx-auto justify-center bg-blue-600">
        <header className="sticky bg-background w-full py-4 top-0 justify-between inline-flex z-10 drop-shadow-md">
            <div className="justify-between items-center flex w-11/12 mx-auto">
                <div className="w-[100px] h-[42.38px] relative">
                    <img
                        className="hidden dark:block w-[100px] h-[42.38px] left-0 top-0 absolute"
                        alt="logo"
                        src="./cdmsmith_logo.png"
                    />
                    <img
                        className="block dark:hidden w-[100px] h-[42.38px] left-0 top-0 absolute"
                        alt="logo"
                        src="./cdmsmith_logo_light.png"
                    />
                </div>
                <div className="app-header-icons flex flex-row gap-3 h-3 items-center justify-center">
                    <h2 className="text-5xl font-bold text-center bg-clip-text text-white">
                        Gen AI {/* Placeholder text */}
                    </h2>
                </div>
                <div className="app-header-icons flex flex-row gap-3 h-6">
                    {/* <DarkToggle /> */}
                </div>
            </div>
        </header>
    </div>
}

export default Header;